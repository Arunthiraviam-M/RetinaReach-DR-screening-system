# Dataset Folder — Where YOUR Data Goes

This folder is where **you** place your fundus/OCT dataset. Nothing in
this repo ships with real patient images — that is intentional and by
design (PHI/privacy).

## Folder layout expected by the training script

```
dataset/
├── train/
│   ├── 0/            # ICDR Grade 0 — No DR
│   │   ├── img001.jpg
│   │   └── ...
│   ├── 1/            # Grade 1 — Mild NPDR
│   ├── 2/            # Grade 2 — Moderate NPDR
│   ├── 3/            # Grade 3 — Severe NPDR
│   └── 4/            # Grade 4 — Proliferative DR
├── val/
│   ├── 0/ ... 4/      # same structure, held-out validation split
├── fundus/            # (optional) raw incoming fundus captures, ungraded
├── oct/                # (optional) raw incoming OCT captures
└── samples/            # a few anonymized/sample images for quick UI testing
```

This is the standard `torchvision.datasets.ImageFolder` layout, which
`scripts/train_model_template.py` reads directly.

## If your dataset is a public one (APTOS 2019 / EyePACS / Messidor / IDRiD)

Each of these ships as a CSV of `image_id, grade` plus a flat folder of
images. Convert to the folder-per-class layout above with a script like:

```python
import pandas as pd, shutil, os

df = pd.read_csv("train.csv")  # columns: id_code, diagnosis
for _, row in df.iterrows():
    grade = str(row["diagnosis"])
    os.makedirs(f"dataset/train/{grade}", exist_ok=True)
    shutil.copy(f"raw_images/{row['id_code']}.png", f"dataset/train/{grade}/{row['id_code']}.png")
```

Adjust column names to match whichever dataset you're using, and split off
~15-20% into `dataset/val/` before training (e.g. with
`sklearn.model_selection.train_test_split`, stratified by grade).

## Then train

```bash
cd scripts
python train_model_template.py --data-dir ../dataset --epochs 20
```

This produces `ml_models/weights/dr_classifier.pt`, which the backend
picks up automatically the next time it starts (see
`ml_models/weights/README.md`).

## Using `dataset/samples/`

Drop 5-10 representative fundus images here (ideally already de-identified)
if you just want to click through the app's upload → analyze → report flow
without waiting on a full training run. The heuristic grader
(`backend/app/services/grading.py`) will analyze them immediately using
real OpenCV lesion detection — no trained model required to see the whole
platform working end-to-end.

## Privacy reminder

Do not commit real patient images to version control. Add `dataset/train`,
`dataset/val`, `dataset/fundus`, and `dataset/oct` to `.gitignore` if you
plan to push this repo anywhere beyond your own machine (already done in
the root `.gitignore`).
