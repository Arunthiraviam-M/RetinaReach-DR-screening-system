from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.patient import Patient
from app.models.study import Study
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class RecentArrival(BaseModel):
    patient_id: str
    patient_code: str
    patient_name: str
    village: str | None
    district: str | None
    arrival_time: datetime
    study_id: str | None
    status: str
    dr_grade_label: str | None
    referable_dr: bool | None


class DashboardStats(BaseModel):
    total_patients: int
    patients_today: int
    studies_pending_review: int
    studies_analyzed_today: int
    referable_cases_today: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_arrivals: list[RecentArrival]


class DistrictStat(BaseModel):
    district: str
    total_patients: int
    referable_cases: int


@router.get("", response_model=DashboardResponse)
async def get_dashboard(limit: int = 15, user: User = Depends(get_current_user)):
    IST = ZoneInfo("Asia/Kolkata")
    now = datetime.now(IST)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_patients = await Patient.find().count()
    patients_today = await Patient.find(Patient.created_at >= start_of_day).count()

    recent_studies = await Study.find().sort("-created_at").limit(limit).to_list()
    arrivals: list[RecentArrival] = []
    referable_today = 0
    analyzed_today = 0
    pending_review = 0

    for study in recent_studies:
        patient = await Patient.get(study.patient_id)
        if not patient:
            continue
        grading = study.grading_result
        arrivals.append(
            RecentArrival(
                patient_id=study.patient_id,
                patient_code=study.patient_code,
                patient_name=patient.full_name,
                village=patient.village,
                district=patient.district,
                arrival_time=study.created_at,
                study_id=str(study.id),
                status=study.status.value,
                dr_grade_label=grading.dr_grade_label if grading else None,
                referable_dr=grading.referable_dr if grading else None,
            )
        )
        if study.status.value != "analyzed":
            pending_review += 1

        if study.analyzed_at:
            analyzed_at = study.analyzed_at

            # MongoDB may return UTC datetimes without timezone information.
            if analyzed_at.tzinfo is None:
                analyzed_at = analyzed_at.replace(tzinfo=timezone.utc)

            analyzed_at = analyzed_at.astimezone(IST)

            if analyzed_at >= start_of_day:
                analyzed_today += 1
                if grading and grading.referable_dr:
                    referable_today += 1

    stats = DashboardStats(
        total_patients=total_patients,
        patients_today=patients_today,
        studies_pending_review=pending_review,
        studies_analyzed_today=analyzed_today,
        referable_cases_today=referable_today,
    )

    return DashboardResponse(stats=stats, recent_arrivals=arrivals)


@router.get("/district-report", response_model=list[DistrictStat])
async def district_report(user: User = Depends(get_current_user)):
    patients = await Patient.find().to_list()
    district_counter: Counter[str] = Counter()
    for p in patients:
        district_counter[p.district or "Unspecified"] += 1

    studies = await Study.find().to_list()
    referable_by_district: Counter[str] = Counter()
    patient_district_map = {str(p.id): (p.district or "Unspecified") for p in patients}
    for s in studies:
        if s.grading_result and s.grading_result.referable_dr:
            district = patient_district_map.get(s.patient_id, "Unspecified")
            referable_by_district[district] += 1

    return [
        DistrictStat(district=d, total_patients=count, referable_cases=referable_by_district.get(d, 0))
        for d, count in sorted(district_counter.items(), key=lambda x: -x[1])
    ]
