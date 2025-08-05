"""Mission and progress related Pydantic models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .goal import Mission


class MissionStatus(BaseModel):
    """Mission with status."""
    id: str
    status: str  # completed, pending, etc.
    points: int


class ProgressResponse(BaseModel):
    """Response for progress endpoint."""
    points_total: int
    missions: List[MissionStatus]
    call_unlocked: bool


class MissionArtifact(BaseModel):
    """Mission completion artifact."""
    answer: str
    # Can contain additional fields as needed


class CompleteMissionRequest(BaseModel):
    """Request to complete a mission."""
    mission_id: str
    artifact: MissionArtifact


class CompleteMissionResponse(BaseModel):
    """Response for mission completion."""
    points_awarded: int
    points_total: int
    call_unlocked: bool
    next_mission: Optional[Mission] = None


class UnlockStatusResponse(BaseModel):
    """Response for unlock status check."""
    call_unlocked: bool