from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.core.deps import get_current_user
from app.models.patient import Patient
from app.models.schemas_clinical import ImageAssetOut, StudyOut, StudySummaryOut
from app.models.study import (
    ImageAsset,
    ImageModality,
    Study,
    StudyStatus,
)
from app.models.user import User
from app.services import gradcam, grading as grading_service
from app.services.iqa import (
    assess_quality,
    bgr_to_encoded_bytes,
    enhance_image,
    load_image_bytes_to_bgr,
    resize_for_display,
)
from app.services.segmentation import analyze_lesions
from app.utils.audit import log_action
from app.utils.storage import absolute_path, new_filename, save_bytes, url_for_path

router = APIRouter(prefix="/studies", tags=["Studies"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB per image


async def _image_asset_out(asset: ImageAsset) -> ImageAssetOut:
    return ImageAssetOut(
        id=str(asset.id),
        modality=asset.modality,
        laterality=asset.laterality.value if asset.laterality else None,
        original_url=url_for_path(asset.original_path) or "",
        enhanced_url=url_for_path(asset.enhanced_path),
        gradcam_url=url_for_path(asset.gradcam_path),
        quality=asset.quality,
    )


async def _study_to_out(study: Study, images: list[ImageAsset]) -> StudyOut:
    image_outs = [await _image_asset_out(img) for img in images]
    return StudyOut(
        id=str(study.id),
        patient_id=study.patient_id,
        patient_code=study.patient_code,
        status=study.status,
        images=image_outs,
        grading_result=study.grading_result,
        created_at=study.created_at,
        analyzed_at=study.analyzed_at,
    )


@router.post("", response_model=StudyOut, status_code=201)
async def create_study(patient_id: str, user: User = Depends(get_current_user)):
    patient = await Patient.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    study = Study(
        patient_id=patient_id,
        patient_code=patient.patient_code,
        created_by=str(user.id),
    )
    await study.insert()
    return await _study_to_out(study, [])


@router.post("/{study_id}/upload", response_model=StudyOut)
async def upload_image(
    study_id: str,
    modality: ImageModality,
    laterality: str | None = None,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    study = await Study.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 15MB limit.")

    try:
        bgr = load_image_bytes_to_bgr(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 1. Image Quality Assessment
    quality = assess_quality(bgr)

    # 2. Adaptive enhancement if borderline
    enhanced_path = None
    working_image = bgr

    if quality.verdict.value == "borderline_enhanced":
        enhanced_bgr, steps_applied = enhance_image(bgr)
        quality.enhancement_applied = steps_applied
        working_image = enhanced_bgr

    # 3. Save original (standardized to 400x300 for consistent on-screen sizing)
    original_filename = new_filename("orig", ".jpg")
    original_display = resize_for_display(bgr)
    original_path = save_bytes(
        "originals",
        original_filename,
        bgr_to_encoded_bytes(original_display),
    )

    if quality.verdict.value == "borderline_enhanced":
        enhanced_filename = new_filename("enh", ".jpg")
        enhanced_display = resize_for_display(working_image)
        enhanced_path = save_bytes(
            "enhanced",
            enhanced_filename,
            bgr_to_encoded_bytes(enhanced_display),
        )

    # Check whether this study already has an image for the same
    # modality + eye. If yes, replace that current image instead
    # of creating a duplicate slot.
    existing_asset = await ImageAsset.find_one(
        ImageAsset.study_id == study_id,
        ImageAsset.modality == modality,
        ImageAsset.laterality == laterality,
    )

    if existing_asset:
        existing_asset.original_path = original_path
        existing_asset.enhanced_path = enhanced_path
        existing_asset.gradcam_path = None
        existing_asset.quality = quality
        existing_asset.uploaded_at = datetime.now(timezone.utc)
        await existing_asset.save()

        asset = existing_asset
    else:
        asset = ImageAsset(
            study_id=study_id,
            patient_id=study.patient_id,
            modality=modality,
            laterality=laterality,
            original_path=original_path,
            enhanced_path=enhanced_path,
            quality=quality,
        )
        await asset.insert()

        study.image_ids.append(str(asset.id))

    # A new upload means this Study needs analysis again.
    # Previous Study records are not affected.
    study.status = (
        StudyStatus.QUALITY_CHECKED
        if quality.verdict.value != "ungradeable"
        else StudyStatus.UPLOADED
    )

    await study.save()

    images = await ImageAsset.find(
        ImageAsset.study_id == study_id
    ).to_list()

    return await _study_to_out(study, images)


@router.post("/{study_id}/analyze", response_model=StudyOut)
async def analyze_study(
    study_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    study = await Study.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found.")

    images = await ImageAsset.find(
        ImageAsset.study_id == study_id
    ).to_list()

    fundus_images = [
        img
        for img in images
        if img.modality == ImageModality.FUNDUS
    ]

    if not fundus_images:
        raise HTTPException(
            status_code=400,
            detail="At least one fundus image is required before analysis.",
        )

    gradeable = [
        img
        for img in fundus_images
        if img.quality
        and img.quality.verdict.value != "ungradeable"
    ]

    if not gradeable:
        raise HTTPException(
            status_code=422,
            detail=(
                "All uploaded fundus images are ungradeable. "
                "Please recapture per the quality feedback before analyzing."
            ),
        )

    study.status = StudyStatus.ANALYZING
    await study.save()

    # Use the most recently uploaded/re-uploaded gradeable Fundus image.
    # This ensures that a retaken image becomes the image analyzed
    # when the user explicitly clicks "Analyze New Images".
    primary_image = max(
        gradeable,
        key=lambda img: img.uploaded_at,
    )

    source_path = (
        primary_image.enhanced_path
        or primary_image.original_path
    )

    abs_path = absolute_path(source_path)

    import cv2

    bgr = cv2.imread(abs_path)
    if bgr is None:
        raise HTTPException(
            status_code=500,
            detail="Could not read stored image for analysis.",
        )

    evidence = analyze_lesions(bgr)
    result = grading_service.grade_study(
        abs_path,
        evidence,
    )

    heatmap = gradcam.generate_heatmap_overlay(
        bgr,
        abs_path,
        evidence,
    )

    heatmap_display = resize_for_display(heatmap)

    from app.services.iqa import bgr_to_encoded_bytes as _encode

    gradcam_filename = new_filename("gradcam", ".jpg")
    gradcam_path = save_bytes(
        "gradcam",
        gradcam_filename,
        _encode(heatmap_display),
    )

    primary_image.gradcam_path = gradcam_path
    await primary_image.save()

    study.grading_result = result
    study.status = StudyStatus.ANALYZED
    study.analyzed_at = datetime.now(timezone.utc)
    await study.save()

    await log_action(
        str(user.id),
        user.role.value,
        "study.analyze",
        "study",
        study_id,
        details=(
            f"grade={result.dr_grade.value} "
            f"confidence={result.confidence}"
        ),
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
    )

    images = await ImageAsset.find(
        ImageAsset.study_id == study_id
    ).to_list()

    return await _study_to_out(study, images)


@router.get("/{study_id}", response_model=StudyOut)
async def get_study(
    study_id: str,
    user: User = Depends(get_current_user),
):
    study = await Study.get(study_id)

    if not study:
        raise HTTPException(
            status_code=404,
            detail="Study not found.",
        )

    images = await ImageAsset.find(
        ImageAsset.study_id == study_id
    ).to_list()

    return await _study_to_out(study, images)


@router.get("", response_model=list[StudySummaryOut])
async def list_recent_studies(
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    studies = (
        await Study.find()
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )

    out = []

    for s in studies:
        patient = await Patient.get(s.patient_id)

        out.append(
            StudySummaryOut(
                id=str(s.id),
                patient_id=s.patient_id,
                patient_code=s.patient_code,
                patient_name=(
                    patient.full_name
                    if patient
                    else "Unknown"
                ),
                status=s.status,
                dr_grade=(
                    s.grading_result.dr_grade.value
                    if s.grading_result
                    else None
                ),
                dr_grade_label=(
                    s.grading_result.dr_grade_label
                    if s.grading_result
                    else None
                ),
                referable_dr=(
                    s.grading_result.referable_dr
                    if s.grading_result
                    else None
                ),
                created_at=s.created_at,
            )
        )

    return out