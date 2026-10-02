# RetinaScan — District Diabetic Retinopathy Screening Platform

An explainable, AI-assisted Diabetic Retinopathy (DR) screening system built
for rural/district health programs in India. Health workers at a primary
health centre capture a fundus (and optionally OCT) image; the system checks
image quality, enhances it if needed, grades DR severity (ICDR 0–4) with a
Grad-CAM explanation and plain-language rationale, and produces a
downloadable PDF report — end to end in under two minutes.

---

## 1. What's in this repository

```
dr-screening-system/
├── backend/            FastAPI application (auth, patients, studies, reports, simulation)
│   ├── app/
│   │   ├── core/       settings, JWT/security, auth dependencies
│   │   ├── db/         MongoDB (Beanie/Motor) connection
│   │   ├── models/     Beanie documents + Pydantic request/response schemas
│   │   ├── routers/    API endpoints
│   │   ├── services/   IQA, enhancement, segmentation, grading, Grad-CAM, PDF report, simulation
│   │   └── utils/      storage, audit logging, patient code generator
│   ├── tests/          unit + integration tests
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/           React (Vite) + Tailwind single-page app
│   └── src/
│       ├── pages/      Landing, Login, Register, Dashboard, New Registration,
│       │               Analysis, Report, Patient Database/Detail, Simulation, Reports
│       ├── components/ Sidebar, TopBar, SettingsModal, ImageUploadCard
│       ├── context/    Auth, Theme, Toast
│       ├── i18n/       English / Tamil / Hindi translations
│       └── api/        Axios client + endpoint wrappers
├── ml_models/
│   ├── weights/        <- put your trained .pt files here (see weights/README.md)
│   └── inference/      dr_classifier.py + gradcam_runner.py (real-model hooks)
├── dataset/            <- put YOUR fundus/OCT dataset here (see dataset/README.md)
├── scripts/
│   ├── seed_database.py          demo users/patients for MongoDB
│   └── train_model_template.py   starting point for training your classifier
├── docker-compose.yml
└── README.md           <- you are here
```

## 2. How grading works today (important — read this first)

The brief asked for a PyTorch/MONAI/Grad-CAM pipeline. Training a clinically
valid model requires a labeled dataset, which only you have. So the system
ships with **two grading paths, chosen automatically**:

1. **Trained-model path** — if `ml_models/weights/dr_classifier.pt` exists,
   the backend loads it and uses real PyTorch inference + real Grad-CAM++.
2. **Heuristic fallback path** (active out of the box) — real OpenCV image
   analysis (optic disc localization, vessel segmentation, microaneurysm/
   hemorrhage/exudate blob detection) feeds a standard ICDR rule-based
   grader, and the "Grad-CAM" is an evidence heatmap built from the actual
   detected lesion locations. **This is not random or fake data** — every
   number comes from real pixel analysis of the uploaded image — but it is
   a rule-based stand-in, not a trained neural network, until you provide
   weights.

This means you can clone this repo, connect your MongoDB, and click through
the entire upload → quality-check → grade → Grad-CAM → PDF report flow
today, with zero training required. When you're ready, drop in trained
weights (see `ml_models/weights/README.md`) and the exact same UI/API
switches to real model inference with no code changes.

## 3. Prerequisites

- Python 3.11+
- Node.js 20+
- A MongoDB Atlas cluster (or local MongoDB) — **this is on you to set up**,
  per your request. Free tier is enough to start:
  1. Create an account at https://www.mongodb.com/cloud/atlas
  2. Create a free (M0) cluster
  3. Database Access → add a database user (username + password)
  4. Network Access → add your IP (or `0.0.0.0/0` for quick local dev)
  5. Connect → "Drivers" → copy the connection string

## 4. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env:
#   MONGODB_URI=<your Atlas connection string>
#   MONGODB_DB_NAME=retinascan
#   JWT_SECRET_KEY=<generate a long random string>

uvicorn app.main:app --reload
```

The API is now live at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

### Seed demo data (optional but recommended)

```bash
# from the repo root, with the backend venv active
python scripts/seed_database.py
```

This creates 3 demo users (admin, ophthalmologist, health worker) and 3 demo
patients. Login credentials are printed to the console — also shown on the
frontend login page.

## 5. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env      # defaults are fine for local dev (uses Vite proxy)
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` and
`/media` to `http://localhost:8000` automatically (see `vite.config.js`), so
no CORS configuration is needed for local development.

## 6. Docker Compose (both services together)

```bash
cp backend/.env.example backend/.env   # then edit MONGODB_URI etc.
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

MongoDB itself is **not** included in `docker-compose.yml` — it points at
whatever `MONGODB_URI` you put in `backend/.env` (your Atlas cluster by
default). See the commented-out `mongo` service in `docker-compose.yml` if
you'd rather run Mongo locally instead of Atlas.

## 7. Uploading your dataset & training a real model

See **`dataset/README.md`** for the exact folder layout expected
(`dataset/train/0..4/`, `dataset/val/0..4/`) and how to convert common
public datasets (APTOS, EyePACS, Messidor, IDRiD) into it.

Once your data is in place:

```bash
cd scripts
python train_model_template.py --data-dir ../dataset --epochs 20
```

This produces `ml_models/weights/dr_classifier.pt`. Restart the backend —
grading and Grad-CAM now use your trained model automatically. See
`ml_models/weights/README.md` and `ml_models/inference/dr_classifier.py`
for full details and how to swap in a different architecture.

**No dataset yet?** Drop 5–10 sample fundus images in `dataset/samples/`
and upload them through the app's "New Registration" flow — the heuristic
grader will analyze them for real (not randomly) so you can see the whole
platform working immediately.

## 8. Using the platform

1. **Register** (`/register`) as a Health Worker or Ophthalmologist —
   fills MongoDB's `users` collection.
2. **Dashboard** — see recent patient arrivals and today's stats.
3. **New Registration** — enter patient details, upload fundus/OCT images.
   Each image is quality-checked live; borderline images are automatically
   enhanced (CLAHE + denoising + illumination normalization); ungradeable
   images show specific recapture instructions.
4. **Continue to Analysis** — runs segmentation + grading + Grad-CAM, then
   shows DR severity in plain language, lesion-level findings, the Grad-CAM
   heatmap, and a referral recommendation with reasoning.
5. **Generate Report** — creates a PDF with all of the above plus the
   images (400×300 standardized), downloadable immediately or later from
   the Patient Database.
6. **Patient Database** — search any patient by name/ID, view their full
   A–Z history, re-download or regenerate any past report.
7. **Workflow Simulation** — a Simulink-style "what-if" tool: adjust
   cameras, GPU nodes, ophthalmologist count, bandwidth, etc. and see the
   effect on daily throughput, bottlenecks, and projected annual capacity
   toward your 100,000+ patients/year target.
8. **Settings** (bottom of sidebar) — switch language (English/Tamil/Hindi),
   light/dark/system theme.

## 9. Sample API requests

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"healthworker@retinascan.demo","password":"Worker@123"}'

# Create a patient (use the access_token from login above)
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test Patient","age":54,"sex":"male","diabetes_status":"known"}'

# Upload a fundus image (multipart)
curl -X POST "http://localhost:8000/api/v1/studies/<STUDY_ID>/upload?modality=fundus&laterality=right" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@/path/to/fundus.jpg"

# Analyze
curl -X POST http://localhost:8000/api/v1/studies/<STUDY_ID>/analyze \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Generate + download report
curl -X POST http://localhost:8000/api/v1/studies/<STUDY_ID>/report \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
curl -X GET http://localhost:8000/api/v1/studies/<STUDY_ID>/report/download \
  -H "Authorization: Bearer <ACCESS_TOKEN>" -o report.pdf
```

Full interactive documentation (all endpoints, schemas, try-it-out) is
always available at `/docs` while the backend is running.

## 10. Running tests

```bash
cd backend
pytest tests/ -v
```

- `test_iqa.py` — image quality assessment + enhancement (pure, no DB needed)
- `test_grading.py` — ICDR rule-based grading logic (pure, no DB needed)
- `test_analyze_flow.py` — full integration test of upload → analyze →
  report → download against a real (throwaway) MongoDB database; skips
  automatically if MongoDB isn't reachable.

## 11. Security & compliance notes

- JWT access (30 min) + refresh (7 day) tokens; role-based access
  (admin / ophthalmologist / health_worker) enforced via FastAPI
  dependencies (`app/core/deps.py`).
- Every grade, report generation, and report download is written to the
  `audit_logs` collection with actor, action, resource, and timestamp.
- Rate limiting is configured (`slowapi`) on upload/analyze endpoints via
  `UPLOAD_RATE_LIMIT` / `ANALYZE_RATE_LIMIT` in `.env`.
- Set `DATA_RETENTION_DAYS` in `.env` to match your program's policy; a
  scheduled cleanup job is not included by default (add a cron/Celery task
  calling into the `Study`/`ImageAsset` collections if you need automatic
  purging).
- Do not commit real patient images or `.env` files — both are covered by
  `.gitignore`.

## 12. Known limitations / next steps

- The heuristic grader is a transparent, rule-based stand-in for a trained
  model — validate against your own labeled data before using grading
  output to make clinical decisions, and prioritize training/plugging in a
  real classifier (Section 7) before any field deployment.
- OCT images are currently stored and displayed but use the same fundus
  grading path; a dedicated MONAI-based OCT model hook can be added
  alongside `ml_models/inference/dr_classifier.py` following the same
  pattern.
- S3 storage is implemented (`STORAGE_BACKEND=s3` in `.env`) but requires
  `boto3` (`pip install boto3`) and your bucket credentials — local disk
  storage is the default and works out of the box.

---

Built for use *alongside*, not in place of, clinical judgement.
