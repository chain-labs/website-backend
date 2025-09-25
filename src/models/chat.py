"""Pydantic models for chat API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

from .mission import MissionStatus, Mission
from .goal import CaseStudy


class ChatContext(BaseModel):
    """Context information about where the user is on the site."""
    page: str = Field(..., description="Page identifier (e.g., 'micro-landing', 'case-study', 'mission-dashboard')")
    section: str = Field(..., description="Subsection/component (e.g., 'hero', 'mission-3', 'progress-widget')")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extra state like caseStudyId or missionId")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    init: Optional[bool] = False
    message: str = Field(..., min_length=0, description="The user's chat message")
    context: ChatContext = Field(..., description="Context about where the user is on the site")


class ChatMessage(BaseModel):
    """Individual chat message in history."""
    role: str = Field(..., description="Either 'user' or 'assistant'")
    message: str = Field(..., description="The message content")
    timestamp: datetime = Field(..., description="When the message was sent")


class ChatProgress(BaseModel):
    """Progress snapshot for chat response."""
    pointsTotal: int = Field(..., description="Total points earned")
    missions: List[MissionStatus] = Field(..., description="All mission statuses")
    callUnlocked: bool = Field(..., description="Whether the free call is unlocked")


class ChatNavigation(BaseModel):
    """Navigation instruction for the frontend."""
    page: str = Field(..., description="Target page to navigate to")
    section: str = Field(..., description="Specific section on that page")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Navigation parameters")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    reply: str = Field(..., description="The assistant's response text")
    history: List[BaseMessage] = Field(..., description="Full chat history")
    followUpMissions: Optional[List[str]] = Field(None, description="New or updated missions")
    updatedProgress: Optional[ChatProgress] = Field(None, description="Progress snapshot for UI sync")
    suggestedRead: Optional[List[str]] = Field(None, description="Recommended case studies")
    navigate: Optional[ChatNavigation] = Field(None, description="Frontend navigation instruction")
    

class ChatHistoryResponse(BaseModel):
    """Response model for chat history retrieval."""

    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Chronological chat history for the current session",
    )

    
