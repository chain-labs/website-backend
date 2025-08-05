"""Session related Pydantic models."""

from typing import List
from pydantic import BaseModel

from .goal import Goal
from .mission import MissionStatus


class SessionResponse(BaseModel):
    """Response for full session hydration."""
    goal: Goal
    missions: List[MissionStatus]
    points_total: int
    call_unlocked: bool