from datetime import datetime
from typing import List, Optional, TypedDict, NotRequired, Dict, Any

from src.models.goal import Hero, Process
from src.models.mission import MissionStatus, Mission


class Session(TypedDict):
    """Session model representing a use session."""
    id: str
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_active: bool


class SessionProgress(TypedDict):
    """Model storing progress details of each session.

    - `missions` now stores full mission objects (dicts) for rendering later.
    - `process` is stored as JSON list of dicts.
    """
    session_id: str
    goal: NotRequired[Optional[str]]
    hero: NotRequired[Hero]
    process: NotRequired[List[Process]]
    why_this_case_studies_were_selected: NotRequired[Optional[str]]
    missions: NotRequired[List[Dict[str, Any]]]
    case_studies: NotRequired[List[str]]
    why: NotRequired[Optional[str]]
    points_total: NotRequired[int]
    call_unlocked: NotRequired[bool]
    created_at: NotRequired[datetime]
    updated_at: NotRequired[datetime]
    call_record: NotRequired[List[Dict[str, str]]]

class SessionTransfer(TypedDict):
    """Model storing transfer links when a user resets a session."""

    id: str
    old_session_id: str
    new_session_id: str
    created_at: NotRequired[datetime]
