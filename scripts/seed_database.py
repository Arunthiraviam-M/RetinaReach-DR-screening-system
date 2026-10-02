"""
Seeds MongoDB Atlas with a few demo records so the app is immediately
explorable after setup: one admin, one ophthalmologist, one health worker,
a handful of patients, and one saved workflow-simulation scenario.

Run from the backend/ folder (with your virtualenv active and .env
configured):

    python -m scripts.seed_database

(or `cd backend && python ../scripts/seed_database.py` — path-independent,
see sys.path handling below)
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.patient import DiabetesStatus, Patient, Sex
from app.models.report import Report
from app.models.simulation import SimulationScenario
from app.models.study import Study
from app.models.user import User, UserRole
from app.services.simulation_engine import compute_scenario


async def seed() -> None:
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    await init_beanie(
        database=db,
        document_models=[User, Patient, Study, Report, SimulationScenario, AuditLog],
    )

    print(f"Seeding database '{settings.MONGODB_DB_NAME}' at {settings.MONGODB_URI[:40]}...")

    # ---- Users ----
    demo_users = [
        {
            "name": "Dr. Ananya Rao",
            "email": "admin@retinascan.demo",
            "password": "Admin@123",
            "role": UserRole.ADMIN,
            "facility_name": "District Program Office",
            "district": "Villupuram",
        },
        {
            "name": "Dr. Karthik Subramaniam",
            "email": "ophthalmologist@retinascan.demo",
            "password": "Doctor@123",
            "role": UserRole.OPHTHALMOLOGIST,
            "facility_name": "Government Eye Hospital",
            "district": "Villupuram",
        },
        {
            "name": "Priya Lakshmi",
            "email": "healthworker@retinascan.demo",
            "password": "Worker@123",
            "role": UserRole.HEALTH_WORKER,
            "facility_name": "Primary Health Centre, Kandamangalam",
            "district": "Villupuram",
        },
    ]

    user_ids = {}
    for u in demo_users:
        existing = await User.find_one(User.email == u["email"])
        if existing:
            user_ids[u["role"].value] = str(existing.id)
            continue
        user = User(
            name=u["name"],
            email=u["email"],
            hashed_password=hash_password(u["password"]),
            role=u["role"],
            facility_name=u["facility_name"],
            district=u["district"],
            phone="9800000000",
            address="Rural Health Office, Villupuram District, Tamil Nadu",
        )
        await user.insert()
        user_ids[u["role"].value] = str(user.id)
        print(f"  Created user: {u['email']} / {u['password']}")

    health_worker_id = user_ids.get(UserRole.HEALTH_WORKER.value)

    # ---- Patients ----
    demo_patients = [
        {
            "patient_code": "RS-2026-000001",
            "full_name": "Murugan Selvam",
            "age": 58,
            "sex": Sex.MALE,
            "village": "Kandamangalam",
            "district": "Villupuram",
            "diabetes_status": DiabetesStatus.KNOWN,
            "diabetes_duration_years": 12,
            "hba1c": 8.4,
        },
        {
            "patient_code": "RS-2026-000002",
            "full_name": "Kamala Devi",
            "age": 63,
            "sex": Sex.FEMALE,
            "village": "Thiruvennainallur",
            "district": "Villupuram",
            "diabetes_status": DiabetesStatus.KNOWN,
            "diabetes_duration_years": 6,
            "hba1c": 7.1,
        },
        {
            "patient_code": "RS-2026-000003",
            "full_name": "Ravi Kumar",
            "age": 45,
            "sex": Sex.MALE,
            "village": "Ulundurpet",
            "district": "Kallakurichi",
            "diabetes_status": DiabetesStatus.UNKNOWN,
        },
    ]

    for p in demo_patients:
        existing = await Patient.find_one(Patient.patient_code == p["patient_code"])
        if existing:
            continue
        patient = Patient(registered_by=health_worker_id or "seed", state="Tamil Nadu", **p)
        await patient.insert()
        print(f"  Created patient: {p['patient_code']} - {p['full_name']}")

    # ---- Simulation scenario ----
    existing_scenario = await SimulationScenario.find_one(SimulationScenario.name == "District Baseline (Demo)")
    if not existing_scenario:
        scenario = SimulationScenario(
            name="District Baseline (Demo)",
            created_by=user_ids.get(UserRole.ADMIN.value, "seed"),
            num_cameras=12,
            images_per_camera_per_day=35,
            gpu_nodes=2,
            ophthalmologists=3,
        )
        scenario = compute_scenario(scenario)
        await scenario.insert()
        print("  Created baseline workflow simulation scenario")

    print("\nSeeding complete. Demo logins:")
    for u in demo_users:
        print(f"  {u['role'].value:>16}: {u['email']} / {u['password']}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
