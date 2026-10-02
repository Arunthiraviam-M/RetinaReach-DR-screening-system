"""
Real Grad-CAM++ generation against the trained classifier's last
convolutional layer. Used automatically once dr_classifier.py's weights
file exists (see grading.py / gradcam.py for the fallback logic when it
doesn't).
"""
from __future__ import annotations

import cv2
import numpy as np
import torch
from PIL import Image
from pytorch_grad_cam import GradCAMPlusPlus
from pytorch_grad_cam.utils.image import show_cam_on_image

from ml_models.inference.dr_classifier import _load_model, _preprocess


def generate_gradcam(image_path: str, weights_path: str, device: str = "cpu") -> np.ndarray:
    model = _load_model(weights_path, device)

    # EfficientNet-B3's last conv block — adjust if you swapped architectures
    # in dr_classifier.py's _build_model().
    target_layers = [model.features[-1]]

    image = Image.open(image_path).convert("RGB")
    input_tensor = _preprocess(image).unsqueeze(0).to(device)

    rgb_img = np.array(image.resize((300, 300))).astype(np.float32) / 255.0

    with GradCAMPlusPlus(model=model, target_layers=target_layers) as cam:
        grayscale_cam = cam(input_tensor=input_tensor)[0]
        visualization = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)

    return cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR)
