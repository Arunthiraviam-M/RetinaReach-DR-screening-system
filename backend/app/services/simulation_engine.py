"""
Simulink-inspired workflow simulation.

Models the district screening pipeline as a simple queueing/rate model:
  Cameras (acquisition) -> Network (bandwidth) -> GPU nodes (processing)
  -> Ophthalmologist review -> Report out

Every formula is a straightforward, explainable rate calculation (no black
box) so program managers can trust and explain the "what-if" projections.
"""
from __future__ import annotations

from app.models.simulation import SimulationScenario


def compute_scenario(s: SimulationScenario) -> SimulationScenario:
    # Acquisition
    daily_images = s.num_cameras * s.images_per_camera_per_day

    # Bandwidth: total MB/day generated vs uplink capacity over working hours
    working_seconds = s.working_hours_per_day * 3600
    bandwidth_required_mbps = (daily_images * s.avg_image_size_mb * 8) / working_seconds
    bandwidth_bottleneck = bandwidth_required_mbps > s.uplink_bandwidth_mbps

    # Processing throughput: GPU nodes running inference sequentially
    processing_capacity_per_day = (working_seconds / s.avg_inference_seconds_per_image) * s.gpu_nodes

    # Review capacity: ophthalmologists validating AI output
    review_capacity_per_day = (working_seconds / s.avg_review_seconds_per_case) * s.ophthalmologists

    # Effective daily throughput is bounded by the tightest stage of the pipeline
    effective_daily_throughput = min(daily_images, processing_capacity_per_day, review_capacity_per_day)

    processing_bottleneck = processing_capacity_per_day < daily_images
    review_bottleneck = review_capacity_per_day < daily_images

    # Average turnaround: acquisition wait + processing wait + review wait,
    # approximated via simple utilization-based queueing (M/M/1-ish).
    def wait_minutes(capacity_per_day: float, load_per_day: float, service_seconds: float) -> float:
        if capacity_per_day <= 0:
            return float("inf")
        utilization = min(load_per_day / capacity_per_day, 0.98)
        base_service_minutes = service_seconds / 60
        return base_service_minutes / max(1 - utilization, 0.02)

    processing_wait = wait_minutes(processing_capacity_per_day, daily_images, s.avg_inference_seconds_per_image)
    review_wait = wait_minutes(review_capacity_per_day, daily_images, s.avg_review_seconds_per_case)
    avg_turnaround_minutes = processing_wait + review_wait

    annual_capacity = effective_daily_throughput * 300  # ~300 operating days/year

    s.daily_images_generated = round(daily_images, 1)
    s.daily_processing_capacity = round(processing_capacity_per_day, 1)
    s.daily_review_capacity = round(review_capacity_per_day, 1)
    s.bandwidth_required_mbps = round(bandwidth_required_mbps, 2)
    s.bandwidth_bottleneck = bandwidth_bottleneck
    s.processing_bottleneck = processing_bottleneck
    s.review_bottleneck = review_bottleneck
    s.avg_turnaround_minutes = round(avg_turnaround_minutes, 1)
    s.annual_capacity = round(annual_capacity, 0)
    s.meets_target = annual_capacity >= s.target_annual_patients

    return s
