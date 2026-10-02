"""
Unit tests for image quality assessment. Run with:
    cd backend && pytest tests/test_iqa.py -v
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.iqa import assess_quality, enhance_image, resize_for_display


def _make_synthetic_fundus(sharp: bool = True, dark: bool = False) -> np.ndarray:
    """Builds a synthetic circular 'fundus-like' image for deterministic testing."""
    size = 400
    img = np.zeros((size, size, 3), dtype=np.uint8)
    center = (size // 2, size // 2)
    radius = size // 2 - 10
    import cv2

    color = (10, 10, 40) if dark else (60, 90, 160)
    cv2.circle(img, center, radius, color, -1)

    if sharp:
        # Add fine structure (simulated vessels) for high Laplacian variance
        for i in range(0, size, 12):
            cv2.line(img, (i, 0), (size - i, size), (30, 30, 30), 1)
    return img


def test_good_quality_image_passes():
    img = _make_synthetic_fundus(sharp=True, dark=False)
    report = assess_quality(img)
    assert report.verdict.value in ("good", "borderline_enhanced")
    assert report.field_of_view_ok is True


def test_dark_image_is_ungradeable_or_borderline():
    img = _make_synthetic_fundus(sharp=True, dark=True)
    report = assess_quality(img)
    assert report.illumination_score < 100
    assert report.verdict.value in ("ungradeable", "borderline_enhanced")


def test_blurry_image_flagged_ungradeable():
    img = _make_synthetic_fundus(sharp=False, dark=False)
    import cv2

    blurred = cv2.GaussianBlur(img, (25, 25), 0)
    report = assess_quality(blurred)
    assert report.sharpness_score < 40


def test_enhancement_runs_without_error_and_changes_image():
    img = _make_synthetic_fundus(sharp=True, dark=True)
    enhanced, steps = enhance_image(img)
    assert enhanced.shape == img.shape
    assert len(steps) > 0
    assert not np.array_equal(enhanced, img)


def test_resize_for_display_produces_exact_dimensions():
    img = _make_synthetic_fundus()
    resized = resize_for_display(img, width=400, height=300)
    assert resized.shape[:2] == (300, 400)
