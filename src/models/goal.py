"""Goal and personalization related Pydantic models."""

from token import EQUAL
from typing import List
from pydantic import BaseModel
from datetime import datetime

class Mission(BaseModel):
    """Mission model."""
    id: str
    title: str
    category: str
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


class AssistantMessage(BaseModel): 
    message: str
    datetime: datetime

class History(BaseModel):
    role: str
    message: str
    datetime: datetime


class GoalResponse(BaseModel):
    """Response for goal submission."""
    assistantMessage: AssistantMessage
    history: List[History]


class ClarifyRequest(BaseModel):
    """Request to clarify a goal."""
    clarification: str

class Hero(BaseModel):
    title: str
    description: str


class Process(BaseModel):
    name: str
    description: str


class ClarifyMission(BaseModel):
    """Mission model for Clarify Response."""
    id: str
    title: str
    description: str
    points: int


class ClarifyResponse(BaseModel):
    """Response model for goal clarification."""
    hero: dict
    process: List[dict]
    goal: str
    caseStudies: List[dict]
    whyThisCaseStudiesWereSelected: str
    missions: List[ClarifyMission]  # Use ClarifyMission here
    why: str
