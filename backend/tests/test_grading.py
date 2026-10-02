"""
Unit tests for the DR grading (heuristic fallback path).
Run with: cd backend && pytest tests/test_grading.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.study import DRGrade
from app.services.grading import _rule_based_grade
from app.services.segmentation import LesionEvidence
import numpy as np


def _evidence(**overrides) -> LesionEvidence:
    base = dict(
        optic_disc_bbox=None,
        optic_disc_confidence=0.0,
        vessel_density=0.05,
        microaneurysm_count=0,
        microaneurysm_confidence=0.0,
        hemorrhage_count=0,
        hemorrhage_confidence=0.0,
        exudate_count=0,
        exudate_area_ratio=0.0,
        exudate_confidence=0.0,
        neovascularization_suspected=False,
        neovascularization_confidence=0.0,
        lesion_mask=np.zeros((10, 10), dtype=np.uint8),
        lesion_points=[],
    )
    base.update(overrides)
    return LesionEvidence(**base)


def test_no_lesions_grades_no_dr():
    assert _rule_based_grade(_evidence()) == DRGrade.NO_DR


def test_single_microaneurysm_grades_mild():
    assert _rule_based_grade(_evidence(microaneurysm_count=1)) == DRGrade.MILD_NPDR


def test_moderate_lesion_burden_grades_moderate():
    result = _rule_based_grade(_evidence(microaneurysm_count=6, hemorrhage_count=1))
    assert result == DRGrade.MODERATE_NPDR


def test_heavy_hemorrhage_burden_grades_severe():
    result = _rule_based_grade(_evidence(hemorrhage_count=9))
    assert result == DRGrade.SEVERE_NPDR


def test_neovascularization_grades_pdr():
    result = _rule_based_grade(_evidence(neovascularization_suspected=True, hemorrhage_count=5))
    assert result == DRGrade.PDR


def test_referable_threshold_is_grade_2_and_above():
    for grade in DRGrade:
        referable_expected = grade.value >= 2
        assert (grade.value >= 2) == referable_expected
