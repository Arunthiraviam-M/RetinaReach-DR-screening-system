from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import Field


class SimulationScenario(Document):
    """
    Parameters + computed results for the Simulink-inspired workflow
    dashboard. Stored so program managers can save/compare "what-if"
    scenarios (e.g. add cameras, add GPU review nodes).
    """

    name: str
    created_by: str

    # Inputs
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

    # Computed outputs (cached on save for dashboard listing)
    daily_images_generated: Optional[float] = None
    daily_processing_capacity: Optional[float] = None
    daily_review_capacity: Optional[float] = None
    bandwidth_required_mbps: Optional[float] = None
    bandwidth_bottleneck: Optional[bool] = None
    processing_bottleneck: Optional[bool] = None
    review_bottleneck: Optional[bool] = None
    avg_turnaround_minutes: Optional[float] = None
    annual_capacity: Optional[float] = None
    meets_target: Optional[bool] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "simulations"
