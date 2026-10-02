from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.core.deps import get_current_user
from app.models.patient import Patient
from app.models.report import Report
from app.models.schemas_clinical import ReportOut
from app.models.study import ImageAsset, ImageModality, Study
from app.models.user import User
from app.services.report_pdf import build_report_pdf
from app.utils.audit import log_action
from app.utils.storage import absolute_path, new_filename, read_bytes, save_bytes, url_for_path

router = APIRouter(prefix="/studies", tags=["Reports"])


def _report_out(r: Report) -> ReportOut:
    return ReportOut(
        id=str(r.id),
        study_id=r.study_id,
        patient_id=r.patient_id,
        patient_code=r.patient_code,
        dr_grade=r.dr_grade,
        referable_dr=r.referable_dr,
        confidence=r.confidence,
        download_url=url_for_path(r.pdf_path) or "",
        created_at=r.created_at,
    )


@router.post("/{study_id}/report", response_model=ReportOut, status_code=201)
async def generate_report(study_id: str, request: Request, user: User = Depends(get_current_user)):
    study = await Study.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found.")
    if not study.grading_result:
        raise HTTPException(status_code=400, detail="Study has not been analyzed yet.")

    patient = await Patient.get(study.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    images = await ImageAsset.find(ImageAsset.study_id == study_id).to_list()

    # Use the latest uploaded gradeable Fundus image,
    # matching the image selection used during analysis.
    fundus_images = [
        img
        for img in images
        if img.modality == ImageModality.FUNDUS
        and img.quality
        and img.quality.verdict.value != "ungradeable"
    ]

    primary = (
        max(fundus_images, key=lambda img: img.uploaded_at)
        if fundus_images
        else None
    )

    image_paths = {
        "original": absolute_path(primary.original_path) if primary else None,
        "enhanced": absolute_path(primary.enhanced_path) if primary and primary.enhanced_path else None,
        "gradcam": absolute_path(primary.gradcam_path) if primary and primary.gradcam_path else None,
    }

    pdf_bytes = build_report_pdf(patient, study, user.name, image_paths)

    filename = new_filename(f"report_{patient.patient_code}", ".pdf")
    pdf_path = save_bytes("reports", filename, pdf_bytes)

    # Versioning: count prior reports for this study
    prior_count = await Report.find(Report.study_id == study_id).count()

    report = Report(
        study_id=study_id,
        patient_id=study.patient_id,
        patient_code=patient.patient_code,
        generated_by=str(user.id),
        pdf_path=pdf_path,
        dr_grade=study.grading_result.dr_grade.value,
        referable_dr=study.grading_result.referable_dr,
        confidence=study.grading_result.confidence,
        version=prior_count + 1,
    )
    await report.insert()

    await log_action(
        str(user.id), user.role.value, "report.generate", "report", str(report.id),
        ip_address=request.client.host if request.client else None,
    )

    return _report_out(report)


@router.get("/{study_id}/report", response_model=ReportOut)
async def get_latest_report(study_id: str, user: User = Depends(get_current_user)):
    report = await Report.find(Report.study_id == study_id).sort("-created_at").first_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="No report has been generated for this study yet.")
    return _report_out(report)


@router.get("/{study_id}/report/download")
async def download_report(study_id: str, request: Request, user: User = Depends(get_current_user)):
    report = await Report.find(Report.study_id == study_id).sort("-created_at").first_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="No report has been generated for this study yet.")

    report.downloaded_count += 1
    report.last_downloaded_at = datetime.now(timezone.utc)
    await report.save()

    await log_action(
        str(user.id), user.role.value, "report.download", "report", str(report.id),
        ip_address=request.client.host if request.client else None,
    )

    pdf_bytes = read_bytes(report.pdf_path)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report.patient_code}_report.pdf"'},
    )