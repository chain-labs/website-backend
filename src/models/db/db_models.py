from datetime import datetime
from typing import Optional, TypedDict


class Session(TypedDict):
    """Session model representing a use session."""

    id: str
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_active: bool
