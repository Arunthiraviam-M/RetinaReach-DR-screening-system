"""
Explainability heatmap generation.

TRAINED MODEL MODE: if weights are present, uses real Grad-CAM++ (via the
`grad-cam` package) on the actual convolutional feature maps of the
classifier — see ml_models/inference/gradcam_runner.py.

FALLBACK MODE: builds an evidence-based heatmap from the lesion mask
produced by segmentation.py (Gaussian-blurred density of detected
microaneurysms/hemorrhages/exudates), overlaid with a jet colormap. This is
not a neural saliency map, but it is a real, image-derived visualization
that highlights the same regions the rule-based grader used to reach its
decision — so it remains a faithful, non-fake explanation of the output
until a trained model is plugged in.
"""
from __future__ import annotations

import os

import cv2
import numpy as np

from app.core.config import settings
from app.services.segmentation import LesionEvidence


def _model_available() -> bool:
    return os.path.exists(settings.DR_CLASSIFIER_WEIGHTS_PATH)


def _real_gradcam(image_path: str) -> np.ndarray | None:
    try:
        from ml_models.inference.gradcam_runner import generate_gradcam
    except Exception:  # noqa: BLE001
        return None
    try:
        return generate_gradcam(image_path, settings.DR_CLASSIFIER_WEIGHTS_PATH, settings.MODEL_DEVICE)
    except Exception:  # noqa: BLE001
        return None


def _evidence_heatmap(bgr: np.ndarray, evidence: LesionEvidence) -> np.ndarray:
    heat = evidence.lesion_mask.astype(np.float32)

    # Widen each lesion point into a soft Gaussian blob so the heatmap reads
    # like a smooth attention map instead of hard dots.
    heat = cv2.GaussianBlur(heat, (0, 0), sigmaX=15, sigmaY=15)
    if heat.max() > 0:
        heat = heat / heat.max()
    heat_u8 = (heat * 255).astype(np.uint8)

    colored = cv2.applyColorMap(heat_u8, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(bgr, 0.6, colored, 0.4, 0)
    return overlay


def generate_heatmap_overlay(bgr: np.ndarray, image_path: str, evidence: LesionEvidence) -> np.ndarray:
    if _model_available():
        real = _real_gradcam(image_path)
        if real is not None:
            return real
    return _evidence_heatmap(bgr, evidence)
