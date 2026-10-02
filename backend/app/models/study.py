from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

import pymongo
from beanie import Document, Indexed
from pydantic import BaseModel, Field


class EyeLaterality(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class ImageModality(str, Enum):
    FUNDUS = "fundus"
    OCT = "oct"


class QualityVerdict(str, Enum):
    GOOD = "good"
    BORDERLINE_ENHANCED = "borderline_enhanced"
    UNGRADEABLE = "ungradeable"


class StudyStatus(str, Enum):
    UPLOADED = "uploaded"
    QUALITY_CHECKED = "quality_checked"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class DRGrade(int, Enum):
    NO_DR = 0
    MILD_NPDR = 1
    MODERATE_NPDR = 2
    SEVERE_NPDR = 3
    PDR = 4


class LesionFinding(BaseModel):
    lesion_type: str  # microaneurysm | hemorrhage | hard_exudate | soft_exudate | neovascularization
    detected: bool
    count_estimate: int = 0
    confidence: float = 0.0
    description: str = ""


class ImageQualityReport(BaseModel):
    verdict: QualityVerdict
    sharpness_score: float
    illumination_score: float
    noise_score: float
    field_of_view_ok: bool
    enhancement_applied: List[str] = []
    recapture_reasons: List[str] = []
    recapture_instructions: List[str] = []


class ImageAsset(Document):
    """Stored separately from Study to keep binary/paths lightweight and queryable."""

    study_id: str
    patient_id: str
    modality: ImageModality
    laterality: Optional[EyeLaterality] = None
    original_path: str
    enhanced_path: Optional[str] = None
    gradcam_path: Optional[str] = None
    quality: Optional[ImageQualityReport] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "image_assets"
        indexes = [pymongo.IndexModel("study_id"), pymongo.IndexModel("patient_id")]


class GradingResult(BaseModel):
    dr_grade: DRGrade
    dr_grade_label: str
    referable_dr: bool
    confidence: float
    lesions: List[LesionFinding] = []
    rationale_summary: str = ""
    rationale_detailed: str = ""
    recommendation: str = ""
    recommendation_reason: str = ""
    refer_to: str = ""
    model_version: str = "heuristic-v1"


class Study(Document):
    patient_id: Indexed(str)
    patient_code: str
    created_by: str  # user id
    status: StudyStatus = StudyStatus.UPLOADED
    image_ids: List[str] = []
    grading_result: Optional[GradingResult] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analyzed_at: Optional[datetime] = None

    class Settings:
        name = "studies"
        indexes = [
            pymongo.IndexModel("patient_id"),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
            pymongo.IndexModel("status"),
        ]
