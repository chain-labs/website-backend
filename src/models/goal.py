"""Goal and personalization related Pydantic models."""

from typing import List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
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
    description: str
    shortDescription: str
    thumbnail: str


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
    status: str = "pending"  # pending, completed, cancelled
    # Optional artifact payload for completed missions (e.g. user's answer)
    artifact: Optional[Dict[str, Any]] = None


class ClarifyResponse(BaseModel):
    """Response model for goal clarification."""
    hero: Hero
    process: List[Process]
    goal: str
    caseStudies: List[CaseStudy]
    whyThisCaseStudiesWereSelected: str
    missions: List[ClarifyMission]  # Use ClarifyMission here
    why: str
    fallbackToGenericData: bool

class PersonalisedData(BaseModel):
    """Response model for personalised data"""
    hero: Hero
    process: List[Process]
    goal: str
    caseStudies: List[CaseStudy]
    whyThisCaseStudiesWereSelected: str
    missions: List[ClarifyMission]  # Use ClarifyMission here
    why: str
    fallbackToGenericData: bool
    points_total: int
    call_unlocked: bool

class PersonalisedResponse(BaseModel):
    """Response model for personalised data"""
    status: str
    messages: List[BaseMessage]
    personalisation: PersonalisedData


