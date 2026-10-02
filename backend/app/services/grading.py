"""
DR severity grading (ICDR 0-4).

Two modes, selected automatically:

1. TRAINED MODEL MODE — if a weights file exists at
   settings.DR_CLASSIFIER_WEIGHTS_PATH, it is loaded once (cached) and used
   for inference. Wire your real architecture in ml_models/inference/
   dr_classifier.py; this service only needs the output contract
   (grade index 0-4 + per-class probabilities) to stay the same.

2. HEURISTIC FALLBACK MODE — if no weights are present (e.g. fresh clone,
   before you've trained/uploaded a model), grading is derived from the
   real lesion evidence computed in segmentation.py using the standard
   ICDR rule set below. This keeps the whole application fully functional
   end-to-end from day one, with real image-driven — not random — outputs.

Confidence values are passed through temperature scaling so they are not
raw, overconfident softmax outputs (see `_temperature_scale`).
"""
from __future__ import annotations

import math
import os

from app.core.config import settings
from app.models.study import DRGrade, GradingResult, LesionFinding
from app.services.segmentation import LesionEvidence

GRADE_LABELS = {
    DRGrade.NO_DR: "No Diabetic Retinopathy",
    DRGrade.MILD_NPDR: "Mild NPDR (Non-Proliferative DR)",
    DRGrade.MODERATE_NPDR: "Moderate NPDR",
    DRGrade.SEVERE_NPDR: "Severe NPDR",
    DRGrade.PDR: "Proliferative DR (PDR)",
}

_TEMPERATURE = 1.8  # calibration temperature; tune on a held-out validation set


def _temperature_scale(raw_confidence: float) -> float:
    """Softens overconfident scores toward 0.5 using logit temperature scaling."""
    raw_confidence = min(max(raw_confidence, 1e-4), 1 - 1e-4)
    logit = math.log(raw_confidence / (1 - raw_confidence))
    scaled_logit = logit / _TEMPERATURE
    return round(1 / (1 + math.exp(-scaled_logit)), 3)


def _model_available() -> bool:
    return os.path.exists(settings.DR_CLASSIFIER_WEIGHTS_PATH)


def _grade_from_trained_model(image_path: str) -> GradingResult | None:
    """
    Hook for your real PyTorch/MONAI model. See
    ml_models/inference/dr_classifier.py for the expected interface.
    Returns None if the model cannot be loaded, causing automatic fallback.
    """
    try:
        from ml_models.inference.dr_classifier import predict as model_predict
    except Exception:  # noqa: BLE001 - inference module or torch not available
        return None

    try:
        grade_idx, probabilities = model_predict(image_path, settings.DR_CLASSIFIER_WEIGHTS_PATH, settings.MODEL_DEVICE)
    except Exception:  # noqa: BLE001 - any inference failure -> safe fallback
        return None

    grade = DRGrade(grade_idx)
    confidence = _temperature_scale(float(max(probabilities)))
    return GradingResult(
        dr_grade=grade,
        dr_grade_label=GRADE_LABELS[grade],
        referable_dr=grade_idx >= 2,
        confidence=confidence,
        model_version="trained-model-v1",
    )


def _rule_based_grade(evidence: LesionEvidence) -> DRGrade:
    """Standard ICDR severity rule-of-thumb from lesion burden."""
    if evidence.neovascularization_suspected:
        return DRGrade.PDR
    if evidence.hemorrhage_count >= 8 or evidence.exudate_area_ratio > 0.02:
        return DRGrade.SEVERE_NPDR
    if evidence.hemorrhage_count >= 2 or evidence.exudate_count >= 3 or evidence.microaneurysm_count >= 6:
        return DRGrade.MODERATE_NPDR
    if evidence.microaneurysm_count >= 1:
        return DRGrade.MILD_NPDR
    return DRGrade.NO_DR


def _build_lesion_findings(evidence: LesionEvidence) -> list[LesionFinding]:
    return [
        LesionFinding(
            lesion_type="microaneurysm",
            detected=evidence.microaneurysm_count > 0,
            count_estimate=evidence.microaneurysm_count,
            confidence=evidence.microaneurysm_confidence,
            description=(
                f"{evidence.microaneurysm_count} small dark round spot(s) consistent with "
                "microaneurysms — tiny bulges in the retina's smallest blood vessels."
                if evidence.microaneurysm_count
                else "No microaneurysms detected."
            ),
        ),
        LesionFinding(
            lesion_type="hemorrhage",
            detected=evidence.hemorrhage_count > 0,
            count_estimate=evidence.hemorrhage_count,
            confidence=evidence.hemorrhage_confidence,
            description=(
                f"{evidence.hemorrhage_count} larger dark blot/dot-shaped area(s) consistent with "
                "retinal hemorrhages — small bleeds within the retina."
                if evidence.hemorrhage_count
                else "No hemorrhages detected."
            ),
        ),
        LesionFinding(
            lesion_type="hard_exudate",
            detected=evidence.exudate_count > 0,
            count_estimate=evidence.exudate_count,
            confidence=evidence.exudate_confidence,
            description=(
                f"{evidence.exudate_count} yellow-white patch(es) consistent with exudates — "
                "fatty deposits leaking from damaged vessels."
                if evidence.exudate_count
                else "No exudates detected."
            ),
        ),
        LesionFinding(
            lesion_type="neovascularization",
            detected=evidence.neovascularization_suspected,
            count_estimate=1 if evidence.neovascularization_suspected else 0,
            confidence=evidence.neovascularization_confidence,
            description=(
                "Abnormal new vessel growth pattern suspected — a sign of advanced (proliferative) disease."
                if evidence.neovascularization_suspected
                else "No neovascularization suspected."
            ),
        ),
    ]


def _plain_language_rationale(grade: DRGrade, evidence: LesionEvidence) -> tuple[str, str]:
    """Returns (short_summary, detailed_explanation) in plain, non-jargon language first."""
    if grade == DRGrade.NO_DR:
        short = "The retina looks healthy — no signs of diabetic damage were found."
        detail = (
            "No microaneurysms, bleeding spots, or fatty deposits were detected on the retina. "
            "This means the blood vessels at the back of the eye currently show no visible "
            "damage from diabetes. Continue routine yearly screening."
        )
    elif grade == DRGrade.MILD_NPDR:
        short = "Very early, mild changes were found — this needs watching, not urgent action."
        detail = (
            f"We found {evidence.microaneurysm_count} tiny weak spot(s) (microaneurysms) in the "
            "smallest blood vessels of the retina. This is the earliest stage of diabetic eye "
            "damage. It usually does not affect vision yet, but the patient should be "
            "re-checked sooner than the standard yearly interval to catch any progression."
        )
    elif grade == DRGrade.MODERATE_NPDR:
        short = "Moderate changes were found — an eye specialist should review this soon."
        detail = (
            f"Along with weak-vessel spots, we found {evidence.hemorrhage_count} bleeding "
            f"area(s) and {evidence.exudate_count} fatty-deposit patch(es). This means the "
            "diabetes is affecting the retina's blood supply more noticeably. It is not an "
            "emergency, but an ophthalmologist should examine the patient within the next few "
            "weeks to decide on treatment or closer monitoring."
        )
    elif grade == DRGrade.SEVERE_NPDR:
        short = "Significant damage found — the patient should see an eye specialist promptly."
        detail = (
            "There is widespread bleeding and/or fluid leakage across the retina. At this "
            "stage there is a real risk of progressing to the most severe form of the disease "
            "within about a year if untreated. The patient should be referred for a full "
            "ophthalmology examination within days, not months."
        )
    else:
        short = "Advanced disease found — this patient needs urgent specialist care."
        detail = (
            "Abnormal new blood vessels appear to be growing on the retina. These vessels are "
            "fragile and can bleed heavily or cause the retina to detach, which can lead to "
            "sudden, severe vision loss. This is the most advanced stage of diabetic "
            "retinopathy and requires urgent referral to a retina specialist, ideally within "
            "the next few days."
        )
    return short, detail


def _recommendation_for(grade: DRGrade) -> tuple[str, str, str]:
    """Returns (recommendation, reason, refer_to) tailored to who should act and why."""
    if grade == DRGrade.NO_DR:
        return (
            "Routine annual screening",
            "No disease detected — yearly screening is the standard interval to catch any "
            "future changes early.",
            "No referral needed. Re-screen with the mobile camera in 12 months.",
        )
    if grade == DRGrade.MILD_NPDR:
        return (
            "Re-screen in 6-12 months",
            "Early-stage changes rarely need treatment yet, but should be tracked to see if "
            "they are progressing.",
            "No urgent referral. A general ophthalmologist visit at the next camp is sufficient.",
        )
    if grade == DRGrade.MODERATE_NPDR:
        return (
            "Refer to an ophthalmologist within 4-6 weeks",
            "Moderate vessel damage carries a meaningful risk of progressing to a sight-"
            "threatening stage if left unchecked.",
            "Refer to the nearest general ophthalmologist or vitreoretinal clinic for a "
            "dilated eye exam and OCT if available.",
        )
    if grade == DRGrade.SEVERE_NPDR:
        return (
            "Refer urgently within 1-2 weeks",
            "High lesion burden means a substantial chance of progressing to proliferative "
            "disease within about a year without treatment.",
            "Refer to a retina specialist / vitreoretinal surgeon for evaluation and possible "
            "laser or anti-VEGF treatment planning.",
        )
    return (
        "Refer immediately (within days)",
        "Suspected new vessel growth carries a high, near-term risk of severe vision loss from "
        "bleeding or retinal detachment.",
        "Urgent referral to a retina specialist / vitreoretinal surgeon capable of laser "
        "photocoagulation or anti-VEGF therapy.",
    )


def grade_study(image_path: str, evidence: LesionEvidence) -> GradingResult:
    if _model_available():
        model_result = _grade_from_trained_model(image_path)
        if model_result is not None:
            model_result.lesions = _build_lesion_findings(evidence)
            short, detail = _plain_language_rationale(model_result.dr_grade, evidence)
            model_result.rationale_summary = short
            model_result.rationale_detailed = detail
            rec, reason, refer_to = _recommendation_for(model_result.dr_grade)
            model_result.recommendation = rec
            model_result.recommendation_reason = reason
            model_result.refer_to = refer_to
            return model_result

    grade = _rule_based_grade(evidence)
    lesions = _build_lesion_findings(evidence)

    # Raw heuristic confidence from how strongly lesion signals agree with the
    # chosen grade, then calibrated via temperature scaling.
    signal_strength = max(
        evidence.microaneurysm_confidence,
        evidence.hemorrhage_confidence,
        evidence.exudate_confidence,
        evidence.neovascularization_confidence,
        0.6,  # baseline confidence for a clean "No DR" call
    )
    confidence = _temperature_scale(signal_strength)

    short, detail = _plain_language_rationale(grade, evidence)
    recommendation, reason, refer_to = _recommendation_for(grade)

    return GradingResult(
        dr_grade=grade,
        dr_grade_label=GRADE_LABELS[grade],
        referable_dr=grade.value >= 2,
        confidence=confidence,
        lesions=lesions,
        rationale_summary=short,
        rationale_detailed=detail,
        recommendation=recommendation,
        recommendation_reason=reason,
        refer_to=refer_to,
        model_version="heuristic-v1 (rule-based on OpenCV lesion evidence)",
    )
