"""In-memory session management for the dummy server."""

from typing import Dict, List, Optional, Set
from datetime import datetime
import uuid

from ..models.goal import Goal, Mission, CaseStudy
from ..models.mission import MissionStatus
from ..models.chat import ChatMessage

from dotenv import load_dotenv
load_dotenv()


class SessionData:
    """Session data structure."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.goal: Optional[Goal] = None
        self.headline: str = ""
        self.missions: List[Mission] = []
        self.recommended_case_studies: List[CaseStudy] = []
        self.points_total: int = 0
        self.completed_missions: Set[str] = set()
        self.created_at = datetime.utcnow()
        self.chat_history: List[ChatMessage] = []
    
    def get_mission_statuses(self) -> List[MissionStatus]:
        """Get missions with their current status."""
        return [
            MissionStatus(
                id=mission.id,
                status="completed" if mission.id in self.completed_missions else "pending",
                points=mission.points
            )
            for mission in self.missions
        ]
    
    def complete_mission(self, mission_id: str) -> Optional[int]:
        """Complete a mission and return points awarded."""
        if mission_id in self.completed_missions:
            return None  # Already completed
        
        mission = next((m for m in self.missions if m.id == mission_id), None)
        if not mission:
            return None  # Mission not found
        
        self.completed_missions.add(mission_id)
        self.points_total += mission.points
        return mission.points
    
    def is_call_unlocked(self) -> bool:
        """Check if call is unlocked (simple rule: 2+ completed missions)."""
        return len(self.completed_missions) >= 2
    
    def add_chat_message(self, role: str, message: str) -> None:
        """Add a message to the chat history."""
        chat_message = ChatMessage(
            role=role,
            message=message,
            timestamp=datetime.utcnow()
        )
        self.chat_history.append(chat_message)
    
    def get_chat_history(self) -> List[ChatMessage]:
        """Get the full chat history."""
        return self.chat_history.copy()


class SessionManager:
    """Manages all session data in memory."""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.revoked_tokens: Set[str] = set()
    
    async def create_session(self, session_id: str) -> SessionData:
        """Create a new session."""
        session_data = SessionData(session_id)
        self.sessions[session_id] = session_data
        return session_data
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    async def revoke_token(self, token: str) -> None:
        """Add token to revoked list."""
        self.revoked_tokens.add(token)
    
    async def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        return token in self.revoked_tokens


# Global session manager instance
session_manager = SessionManager()