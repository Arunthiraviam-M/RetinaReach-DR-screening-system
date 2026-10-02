"""
Trained DR classifier inference interface.

This is the ONE file you need to complete once you have a trained model.
The backend (`backend/app/services/grading.py`) calls `predict()` below —
as long as this function exists and returns the documented shape, the rest
of the application (API, frontend, PDF reports) needs zero changes.

Expected model: a 5-class classifier over ICDR grades 0-4, trained on your
fundus dataset (e.g. EfficientNet-B3/ConvNeXt-Tiny backbone, as referenced
in the project brief). Ordinal regression heads are also fine — just map
your head's output into 5 class probabilities before returning.

--------------------------------------------------------------------------
HOW TO PLUG IN YOUR TRAINED MODEL
--------------------------------------------------------------------------
1. Train your model separately (see scripts/train_model_template.py for a
   starting point) and export weights to:
       ml_models/weights/dr_classifier.pt
   (a plain `torch.save(model.state_dict(), path)` file is expected below;
   adjust `_build_model()` if you export a full model or TorchScript
   instead).

2. Set DR_CLASSIFIER_WEIGHTS_PATH in backend/.env if you used a different
   path or filename.

3. That's it — grading.py automatically detects the file and switches from
   the heuristic fallback to this real model on the next request.
--------------------------------------------------------------------------
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

NUM_CLASSES = 5
IMG_SIZE = 300

_preprocess = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def _build_model() -> nn.Module:
    """
    Default architecture: EfficientNet-B3 backbone with a 5-way classifier
    head, matching the brief's recommended backbones. If you trained a
    different architecture, change this function to match — the state_dict
    keys must line up with what you saved during training.
    """
    model = models.efficientnet_b3(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, NUM_CLASSES)
    return model


@lru_cache(maxsize=1)
def _load_model(weights_path: str, device: str) -> nn.Module:
    model = _build_model()
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


def predict(image_path: str, weights_path: str, device: str = "cpu") -> tuple[int, list[float]]:
    """
    Returns (predicted_grade_index, class_probabilities[5]).
    Raises on any failure — the caller (grading.py) treats an exception as
    "model unavailable" and safely falls back to the heuristic grader.
    """
    model = _load_model(weights_path, device)

    image = Image.open(image_path).convert("RGB")
    tensor = _preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]

    grade_idx = int(np.argmax(probabilities))
    return grade_idx, probabilities.tolist()
