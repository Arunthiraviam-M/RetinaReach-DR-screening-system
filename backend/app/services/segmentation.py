"""
Retinal structure segmentation and lesion detection.

This module performs REAL, deterministic image analysis with OpenCV
(color-space thresholding, morphology, blob/contour detection) to localize
the optic disc, approximate the vessel tree, and flag candidate lesions.

It is intentionally designed as the feature-extraction front-end for a
learned classifier: `grading.py` consumes the LesionEvidence produced here.
When you plug in trained PyTorch/MONAI weights (see ml_models/), replace
the calls in grading.py with your model's outputs — the API/response shape
stays identical so the frontend does not need to change.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class LesionEvidence:
    optic_disc_bbox: tuple[int, int, int, int] | None
    optic_disc_confidence: float
    vessel_density: float  # fraction of frame classified as vessel
    microaneurysm_count: int
    microaneurysm_confidence: float
    hemorrhage_count: int
    hemorrhage_confidence: float
    exudate_count: int
    exudate_area_ratio: float
    exudate_confidence: float
    neovascularization_suspected: bool
    neovascularization_confidence: float
    lesion_mask: np.ndarray = field(repr=False)  # single-channel mask, same size as input
    lesion_points: list[tuple[int, int, int]] = field(default_factory=list)  # x, y, radius (for overlay)


def _detect_optic_disc(bgr: np.ndarray) -> tuple[tuple[int, int, int, int] | None, float]:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
    _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(blurred)

    # The optic disc is the brightest large circular region. Threshold near
    # the max intensity, then take the largest resulting contour.
    _, thresh = cv2.threshold(blurred, max(max_val - 25, 0), 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0.0

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < 50:
        return None, 0.0

    x, y, w, h = cv2.boundingRect(largest)
    frame_area = gray.shape[0] * gray.shape[1]
    plausibility = min(1.0, area / (frame_area * 0.02))  # optic disc ~2% of frame is typical
    confidence = round(0.55 + 0.4 * plausibility, 2)
    return (x, y, w, h), confidence


def _vessel_mask(bgr: np.ndarray) -> np.ndarray:
    # Vessels have highest contrast in the green channel.
    green = bgr[:, :, 1]
    green_eq = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(green)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    blackhat = cv2.morphologyEx(green_eq, cv2.MORPH_BLACKHAT, kernel)
    _, vessels = cv2.threshold(blackhat, 15, 255, cv2.THRESH_BINARY)
    vessels = cv2.medianBlur(vessels, 3)
    return vessels


def _dark_lesion_blobs(bgr: np.ndarray, fov_mask: np.ndarray) -> list[tuple[int, int, int]]:
    """Candidate microaneurysms / hemorrhages: small dark round blobs within the retina."""
    green = bgr[:, :, 1]
    green = cv2.bitwise_and(green, green, mask=fov_mask)
    green_eq = cv2.equalizeHist(green)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    blackhat = cv2.morphologyEx(green_eq, cv2.MORPH_BLACKHAT, kernel)
    _, thresh = cv2.threshold(blackhat, 30, 255, cv2.THRESH_BINARY)
    thresh = cv2.bitwise_and(thresh, thresh, mask=fov_mask)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs = []
    for c in contours:
        area = cv2.contourArea(c)
        if 4 <= area <= 220:  # filters out vessels (elongated/large) and sensor noise (tiny)
            (x, y), radius = cv2.minEnclosingCircle(c)
            perimeter = cv2.arcLength(c, True) or 1.0
            circularity = 4 * np.pi * area / (perimeter**2)
            if circularity > 0.35:  # round-ish, unlike thin vessel segments
                blobs.append((int(x), int(y), max(int(radius), 2)))
    return blobs


def _bright_lesion_regions(bgr: np.ndarray, fov_mask: np.ndarray, optic_disc_bbox) -> tuple[list[tuple[int, int, int]], float]:
    """Candidate hard/soft exudates: yellow-white patches, excluding the optic disc itself."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([15, 40, 170])
    upper = np.array([40, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.bitwise_and(mask, mask, mask=fov_mask)

    if optic_disc_bbox is not None:
        x, y, w, h = optic_disc_bbox
        pad = int(0.3 * max(w, h))
        cv2.rectangle(mask, (max(x - pad, 0), max(y - pad, 0)), (x + w + pad, y + h + pad), 0, -1)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    blobs = []
    total_area = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area >= 6:
            (x, y), radius = cv2.minEnclosingCircle(c)
            blobs.append((int(x), int(y), max(int(radius), 2)))
            total_area += area

    frame_area = bgr.shape[0] * bgr.shape[1]
    area_ratio = total_area / frame_area
    return blobs, area_ratio


def analyze_lesions(bgr: np.ndarray) -> LesionEvidence:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, fov_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)

    optic_disc_bbox, optic_disc_conf = _detect_optic_disc(bgr)

    vessels = _vessel_mask(bgr)
    vessel_density = float(np.count_nonzero(vessels)) / float(vessels.size)

    dark_blobs = _dark_lesion_blobs(bgr, fov_mask)
    bright_blobs, exudate_ratio = _bright_lesion_regions(bgr, fov_mask, optic_disc_bbox)

    # Heuristic split of dark blobs into "microaneurysm-like" (small) vs
    # "hemorrhage-like" (larger, less circular clusters) by radius.
    microaneurysms = [b for b in dark_blobs if b[2] <= 4]
    hemorrhages = [b for b in dark_blobs if b[2] > 4]

    ma_conf = round(min(0.95, 0.5 + 0.02 * len(microaneurysms)), 2) if microaneurysms else 0.0
    hem_conf = round(min(0.95, 0.5 + 0.03 * len(hemorrhages)), 2) if hemorrhages else 0.0
    exu_conf = round(min(0.95, 0.5 + 40 * exudate_ratio), 2) if bright_blobs else 0.0

    # Neovascularization proxy: unusually high, irregular vessel density
    # concentrated near/beyond the optic disc margin. This is a simplified
    # stand-in — replace with a trained detector for clinical deployment.
    neo_suspected = vessel_density > 0.16 and len(hemorrhages) >= 3
    neo_conf = round(min(0.9, vessel_density * 3.0), 2) if neo_suspected else 0.0

    lesion_mask = np.zeros_like(gray)
    lesion_points: list[tuple[int, int, int]] = []
    for x, y, r in dark_blobs + bright_blobs:
        cv2.circle(lesion_mask, (x, y), max(r, 4), 255, -1)
        lesion_points.append((x, y, max(r, 4)))

    return LesionEvidence(
        optic_disc_bbox=optic_disc_bbox,
        optic_disc_confidence=optic_disc_conf,
        vessel_density=round(vessel_density, 4),
        microaneurysm_count=len(microaneurysms),
        microaneurysm_confidence=ma_conf,
        hemorrhage_count=len(hemorrhages),
        hemorrhage_confidence=hem_conf,
        exudate_count=len(bright_blobs),
        exudate_area_ratio=round(exudate_ratio, 5),
        exudate_confidence=exu_conf,
        neovascularization_suspected=neo_suspected,
        neovascularization_confidence=neo_conf,
        lesion_mask=lesion_mask,
        lesion_points=lesion_points,
    )
