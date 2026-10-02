"""
Integration test for the register -> patient -> study -> upload -> analyze
-> report flow, exercised through the real FastAPI app.

This test needs a reachable MongoDB (Atlas or local) — it uses whatever
MONGODB_URI is configured in backend/.env, but writes to a throwaway
database name so it never touches your real data.

Run with: cd backend && pytest tests/test_analyze_flow.py -v -s
Skips automatically if no MongoDB is reachable (e.g. in CI without Atlas
credentials configured).
"""
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytest_plugins = ("pytest_asyncio",)


def _make_test_fundus_bytes() -> bytes:
    import cv2
    import numpy as np

    img = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.circle(img, (200, 200), 190, (60, 90, 160), -1)
    for i in range(0, 400, 10):
        cv2.line(img, (i, 0), (400 - i, 400), (30, 30, 30), 1)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_full_flow(monkeypatch, tmp_path):
    monkeypatch.setenv("MONGODB_DB_NAME", "retinascan_test")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path / "storage"))

    try:
        import motor.motor_asyncio  # noqa: F401
        from httpx import ASGITransport, AsyncClient

        from app.core.config import get_settings

        get_settings.cache_clear()
        from app.main import app

        client = motor.motor_asyncio.AsyncIOMotorClient(get_settings().MONGODB_URI, serverSelectionTimeoutMS=2000)
        await client.admin.command("ping")
    except Exception:
        pytest.skip("MongoDB not reachable — skipping integration test.")
        return

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register
        register_resp = await ac.post(
            "/api/v1/auth/register",
            json={
                "name": "Test Worker",
                "email": f"test_{tmp_path.name}@example.com",
                "password": "TestPass123",
                "address": "Test PHC",
                "role": "health_worker",
            },
        )
        assert register_resp.status_code == 201, register_resp.text
        token = register_resp.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create patient
        patient_resp = await ac.post(
            "/api/v1/patients",
            json={"full_name": "Test Patient", "age": 55, "sex": "male", "diabetes_status": "known"},
            headers=headers,
        )
        assert patient_resp.status_code == 201, patient_resp.text
        patient_id = patient_resp.json()["id"]

        # Create study
        study_resp = await ac.post(f"/api/v1/studies?patient_id={patient_id}", headers=headers)
        assert study_resp.status_code == 201, study_resp.text
        study_id = study_resp.json()["id"]

        # Upload fundus image
        files = {"file": ("test_fundus.jpg", io.BytesIO(_make_test_fundus_bytes()), "image/jpeg")}
        upload_resp = await ac.post(
            f"/api/v1/studies/{study_id}/upload?modality=fundus&laterality=right",
            files=files,
            headers=headers,
        )
        assert upload_resp.status_code == 200, upload_resp.text

        # Analyze
        analyze_resp = await ac.post(f"/api/v1/studies/{study_id}/analyze", headers=headers)
        assert analyze_resp.status_code == 200, analyze_resp.text
        result = analyze_resp.json()
        assert result["grading_result"] is not None
        assert 0 <= result["grading_result"]["dr_grade"] <= 4

        # Generate report
        report_resp = await ac.post(f"/api/v1/studies/{study_id}/report", headers=headers)
        assert report_resp.status_code == 201, report_resp.text

        # Download report
        download_resp = await ac.get(f"/api/v1/studies/{study_id}/report/download", headers=headers)
        assert download_resp.status_code == 200
        assert download_resp.headers["content-type"] == "application/pdf"

        # Cleanup test database
        await client.drop_database("retinascan_test")
