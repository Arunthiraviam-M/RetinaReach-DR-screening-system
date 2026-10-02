# Model Weights

Place your trained model files here:

| File | Used by | Required? |
|---|---|---|
| `dr_classifier.pt` | `ml_models/inference/dr_classifier.py` | Optional — heuristic fallback is used until present |
| `segmentation.pt` | Future: swap into `backend/app/services/segmentation.py` | Optional |
| `oct_model.pt` | Future: OCT-specific grading path | Optional |

**Nothing needs to be here for the app to run.** Without weights, the
system uses the deterministic, OpenCV-based heuristic grader
(`backend/app/services/grading.py` + `segmentation.py`) so you get a fully
functional, end-to-end demo immediately with real (not random) image
analysis.

When you have trained weights:

1. Export with `torch.save(model.state_dict(), "dr_classifier.pt")` (see
   `ml_models/inference/dr_classifier.py` for the exact architecture
   expected, or edit `_build_model()` to match your own).
2. Drop the `.pt` file in this folder.
3. Confirm `backend/.env` → `DR_CLASSIFIER_WEIGHTS_PATH` points at it.
4. Restart the backend. Grading + Grad-CAM now automatically use your real
   model — no other code changes required.
