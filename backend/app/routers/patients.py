from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.deps import get_current_user
from app.models.patient import Patient
from app.models.report import Report
from app.models.schemas_clinical import (
    PatientCreateRequest,
    PatientHistoryOut,
    PatientOut,
    ReportOut,
    StudyOut,
)
from app.models.study import ImageAsset, Study
from app.models.user import User
from app.routers.studies import _study_to_out  # reuse serializer
from app.utils.audit import log_action
from app.utils.codes import generate_patient_code
from app.utils.storage import url_for_path

router = APIRouter(prefix="/patients", tags=["Patients"])


def _patient_out(p: Patient) -> PatientOut:
    return PatientOut(
        id=str(p.id),
        patient_code=p.patient_code,
        full_name=p.full_name,
        age=p.age,
        sex=p.sex,
        phone=p.phone,
        village=p.village,
        district=p.district,
        state=p.state,
        diabetes_status=p.diabetes_status,
        diabetes_duration_years=p.diabetes_duration_years,
        hba1c=p.hba1c,
        created_at=p.created_at,
    )


@router.post("", response_model=PatientOut, status_code=201)
async def create_patient(payload: PatientCreateRequest, request: Request, user: User = Depends(get_current_user)):
    code = await generate_patient_code()
    patient = Patient(
        patient_code=code,
        registered_by=str(user.id),
        **payload.model_dump(),
    )
    await patient.insert()
    await log_action(str(user.id), user.role.value, "patient.create", "patient", str(patient.id), ip_address=request.client.host if request.client else None)
    return _patient_out(patient)


@router.get("", response_model=list[PatientOut])
async def list_patients(
    search: str | None = Query(default=None, description="Search by name or patient code"),
    district: str | None = None,
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
):
    query: dict = {}
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"patient_code": {"$regex": search, "$options": "i"}},
        ]
    if district:
        query["district"] = district

    patients = await Patient.find(query).sort("-created_at").limit(limit).to_list()
    return [_patient_out(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: str, user: User = Depends(get_current_user)):
    patient = await Patient.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return _patient_out(patient)


@router.get("/{patient_id}/history", response_model=PatientHistoryOut)
async def patient_history(patient_id: str, user: User = Depends(get_current_user)):
    patient = await Patient.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    studies = await Study.find(Study.patient_id == patient_id).sort("-created_at").to_list()
    study_outs: list[StudyOut] = []
    for study in studies:
        images = await ImageAsset.find(ImageAsset.study_id == str(study.id)).to_list()
        study_outs.append(await _study_to_out(study, images))

    reports = await Report.find(Report.patient_id == patient_id).sort("-created_at").to_list()
    report_outs = [
        ReportOut(
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
        for r in reports
    ]

    return PatientHistoryOut(patient=_patient_out(patient), studies=study_outs, reports=report_outs)
