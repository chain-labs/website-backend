"""Goal and personalization related Pydantic models."""

from typing import Any, Dict, List
from pydantic import BaseModel


class Mission(BaseModel):
    """Mission model."""
    id: str
    title: str
    points: int
    status: str = "pending"  # pending, completed, cancelled


class CaseStudy(BaseModel):
    """Case study model."""
    id: str
    title: str
    summary: str


class Goal(BaseModel):
    """Structured goal model."""
    # This can be a flexible dict since the spec shows "structured goal"
    # but doesn't specify exact fields
    description: str
    category: str = "general"
    priority: str = "medium"


class GoalRequest(BaseModel):
    """Request to submit a goal."""
    input: str


class GoalResponse(BaseModel):
    """Response for goal submission."""
    session_id: str
    goal: Goal
    missions: List[Mission]
    headline: str
    recommended_case_studies: List[CaseStudy]


class ClarifyRequest(BaseModel):
    """Request to clarify a goal."""
    clarification: str


class ClarifyResponse(BaseModel):
    """Response for goal clarification."""
    goal: Goal
    missions: List[Mission]
    headline: str
    recommended_case_studies: List[CaseStudy]


class PersonalizedResponse(BaseModel):
    """Response for personalized content."""
    headline: str
    goal: Goal
    missions: List[Mission]
    recommended_case_studies: List[CaseStudy]