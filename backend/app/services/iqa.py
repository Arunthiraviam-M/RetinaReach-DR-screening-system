"""
Image Quality Assessment (IQA) and adaptive enhancement.

Every metric here is computed for real from the pixel data with OpenCV —
nothing is faked. Thresholds are configurable constants below; tune them
against your own camera's image distribution (see README "Tuning IQA").
"""
from __future__ import annotations

import cv2
import numpy as np

from app.models.study import ImageQualityReport, QualityVerdict

# ---- Tunable thresholds -----------------------------------------------
SHARPNESS_GOOD = 120.0          # Laplacian variance above this = sharp
SHARPNESS_BORDERLINE = 40.0     # below this = too blurry to enhance away
ILLUMINATION_LOW = 60.0         # mean intensity below this = too dark
ILLUMINATION_HIGH = 210.0       # mean intensity above this = blown out / glare
NOISE_BORDERLINE = 18.0         # estimated noise sigma above this = noisy
MIN_FIELD_OF_VIEW_RATIO = 0.35  # fraction of frame that must be retina, not black border
# -------------------------------------------------------------------------


def _laplacian_sharpness(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _illumination_stats(gray: np.ndarray) -> tuple[float, float]:
    return float(gray.mean()), float(gray.std())


def _estimate_noise_sigma(gray: np.ndarray) -> float:
    """Fast noise estimate via the median absolute deviation of the Laplacian."""
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    sigma = np.median(np.abs(lap)) / 0.6745
    return float(sigma)


def _field_of_view_ratio(gray: np.ndarray) -> float:
    """Estimates what fraction of the frame is actual fundus (non-black) content."""
    _, mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
    return float(np.count_nonzero(mask)) / float(mask.size)


def assess_quality(bgr_image: np.ndarray) -> ImageQualityReport:
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)

    sharpness = _laplacian_sharpness(gray)
    mean_illum, _std_illum = _illumination_stats(gray)
    noise_sigma = _estimate_noise_sigma(gray)
    fov_ratio = _field_of_view_ratio(gray)
    fov_ok = fov_ratio >= MIN_FIELD_OF_VIEW_RATIO

    reasons: list[str] = []
    instructions: list[str] = []

    if sharpness < SHARPNESS_BORDERLINE:
        reasons.append("Image is too blurry to grade reliably.")
        instructions.append("Ask the patient to fixate steadily on the target light and hold still.")
        instructions.append("Clean the camera lens and recheck focus ring before recapturing.")

    if not fov_ok:
        reasons.append("Retina is not adequately centered / too much of the frame is dark border.")
        instructions.append("Re-align the camera so the optic disc and macula are both visible and centered.")

    if mean_illum < ILLUMINATION_LOW:
        reasons.append("Image is underexposed (too dark).")
        instructions.append("Increase flash/illumination intensity slightly and recapture.")
    elif mean_illum > ILLUMINATION_HIGH:
        reasons.append("Image has excessive glare / overexposure.")
        instructions.append("Reduce flash intensity or reposition to avoid corneal reflection, then recapture.")

    if reasons:
        verdict = QualityVerdict.UNGRADEABLE
    elif sharpness < SHARPNESS_GOOD or noise_sigma > NOISE_BORDERLINE or mean_illum < ILLUMINATION_LOW + 25:
        verdict = QualityVerdict.BORDERLINE_ENHANCED
    else:
        verdict = QualityVerdict.GOOD

    return ImageQualityReport(
        verdict=verdict,
        sharpness_score=round(sharpness, 2),
        illumination_score=round(mean_illum, 2),
        noise_score=round(noise_sigma, 2),
        field_of_view_ok=fov_ok,
        enhancement_applied=[],
        recapture_reasons=reasons,
        recapture_instructions=instructions,
    )


def enhance_image(bgr_image: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """
    Applies CLAHE (contrast), illumination normalization, and denoising.
    Returns the enhanced BGR image plus a list of the steps actually applied,
    so the UI/report can be transparent about what was done to the image.
    """
    applied: list[str] = []
    result = bgr_image.copy()

    # 1. Denoise first so CLAHE doesn't amplify sensor noise.
    result = cv2.fastNlMeansDenoisingColored(result, None, h=6, hColor=6, templateWindowSize=7, searchWindowSize=21)
    applied.append("Denoising (Non-local Means)")

    # 2. Illumination normalization + contrast via CLAHE on the L channel (LAB space)
    # preserves color balance of the fundus far better than doing it on RGB directly.
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    lab = cv2.merge((l_channel, a_channel, b_channel))
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    applied.append("CLAHE contrast enhancement")
    applied.append("Illumination normalization (LAB L-channel)")

    # 3. Mild unsharp mask to recover perceived sharpness lost during denoising.
    gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=3)
    result = cv2.addWeighted(result, 1.4, gaussian, -0.4, 0)
    applied.append("Unsharp masking")

    return result, applied


def load_image_bytes_to_bgr(data: bytes) -> np.ndarray:
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image — file may be corrupted or an unsupported format.")
    return image


def bgr_to_encoded_bytes(image: np.ndarray, ext: str = ".jpg") -> bytes:
    ok, buffer = cv2.imencode(ext, image, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise ValueError("Failed to encode image.")
    return buffer.tobytes()


def resize_for_display(image: np.ndarray, width: int = 400, height: int = 300) -> np.ndarray:
    """
    Standardizes every image shown in the UI/report to the fixed 400x300
    display size requested for the platform, preserving aspect ratio with
    letterboxing so lesions are not stretched/distorted.
    """
    target_w, target_h = width, height
    h, w = image.shape[:2]
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    x_off = (target_w - new_w) // 2
    y_off = (target_h - new_h) // 2
    canvas[y_off : y_off + new_h, x_off : x_off + new_w] = resized
    return canvas
