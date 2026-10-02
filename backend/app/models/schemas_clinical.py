from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.patient import DiabetesStatus, Sex
from app.models.study import GradingResult, ImageModality, ImageQualityReport, StudyStatus


class PatientCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    age: int = Field(ge=0, le=120)
    sex: Sex
    phone: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: str = "Tamil Nadu"
    diabetes_status: DiabetesStatus = DiabetesStatus.UNKNOWN
    diabetes_duration_years: Optional[float] = None
    hba1c: Optional[float] = None
    other_conditions: Optional[str] = None


class PatientOut(BaseModel):
    id: str
    patient_code: str
    full_name: str
    age: int
    sex: Sex
    phone: Optional[str]
    village: Optional[str]
    district: Optional[str]
    state: str
    diabetes_status: DiabetesStatus
    diabetes_duration_years: Optional[float]
    hba1c: Optional[float]
    created_at: datetime


class ImageAssetOut(BaseModel):
    id: str
    modality: ImageModality
    laterality: Optional[str]
    original_url: str
    enhanced_url: Optional[str]
    gradcam_url: Optional[str]
    quality: Optional[ImageQualityReport]


class StudyOut(BaseModel):
    id: str
    patient_id: str
    patient_code: str
    status: StudyStatus
    images: List[ImageAssetOut] = []
    grading_result: Optional[GradingResult] = None
    created_at: datetime
    analyzed_at: Optional[datetime]


class StudySummaryOut(BaseModel):
    """Lightweight version for lists/dashboards."""

    id: str
    patient_id: str
    patient_code: str
    patient_name: str
    status: StudyStatus
    dr_grade: Optional[int] = None
    dr_grade_label: Optional[str] = None
    referable_dr: Optional[bool] = None
    created_at: datetime


class ReportOut(BaseModel):
    id: str
    study_id: str
    patient_id: str
    patient_code: str
    dr_grade: int
    referable_dr: bool
    confidence: float
    download_url: str
    created_at: datetime


class PatientHistoryOut(BaseModel):
    patient: PatientOut
    studies: List[StudyOut]
    reports: List[ReportOut]
