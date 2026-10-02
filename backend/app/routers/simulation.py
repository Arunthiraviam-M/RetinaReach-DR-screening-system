from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.simulation import SimulationScenario
from app.models.user import User
from app.services.simulation_engine import compute_scenario

router = APIRouter(prefix="/simulation", tags=["Workflow Simulation"])


class ScenarioInput(BaseModel):
    name: str = "Untitled Scenario"
    num_cameras: int = 10
    images_per_camera_per_day: int = 40
    avg_image_size_mb: float = 3.5
    uplink_bandwidth_mbps: float = 5.0
    gpu_nodes: int = 2
    avg_inference_seconds_per_image: float = 4.0
    ophthalmologists: int = 3
    avg_review_seconds_per_case: float = 25.0
    working_hours_per_day: float = 8.0
    target_annual_patients: int = 100000


@router.post("/workflow", response_model=SimulationScenario)
async def run_scenario(payload: ScenarioInput, user: User = Depends(get_current_user)):
    scenario = SimulationScenario(created_by=str(user.id), **payload.model_dump())
    scenario = compute_scenario(scenario)
    await scenario.insert()
    return scenario


@router.get("/workflow", response_model=list[SimulationScenario])
async def list_scenarios(limit: int = 20, user: User = Depends(get_current_user)):
    return await SimulationScenario.find().sort("-created_at").limit(limit).to_list()


@router.get("/workflow/{scenario_id}", response_model=SimulationScenario)
async def get_scenario(scenario_id: str, user: User = Depends(get_current_user)):
    scenario = await SimulationScenario.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return scenario
