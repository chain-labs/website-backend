"""Session management utilities.

This module provides two layers:
- A lightweight in-memory API (`SessionData`, `SessionManager.create_session`, etc.) that existing
  code and tests rely on.
- DB-backed helpers to persist and retrieve `SessionProgress` for long-lived session state.
"""

from typing import Any, Dict, List, Optional, Set, cast
import traceback
from psycopg.types.json import Json
from datetime import datetime, timezone

from ..models.goal import Goal, Mission, CaseStudy
from ..models.mission import MissionStatus
from ..models.chat import ChatMessage
from ..models.db.db_models import SessionProgress
from ..database import get_connection, transaction


class SessionData:
    """Session data structure for in-memory operations and tests."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.goal: Optional[Goal] = None
        self.headline: str = ""
        self.missions: List[Mission] = []
        self.recommended_case_studies: List[CaseStudy] = []
        self.points_total: int = 0
        self.completed_missions: Set[str] = set()
        self.created_at = datetime.now(timezone.utc)
        self.chat_history: List[ChatMessage] = []

    def get_mission_statuses(self) -> List[MissionStatus]:
        """Get missions with their current status."""
        return [
            MissionStatus(
                id=mission.id,
                status="completed" if mission.id in self.completed_missions else "pending",
                points=mission.points,
            )
            for mission in self.missions
        ]

    def complete_mission(self, mission_id: str) -> Optional[int]:
        """Complete a mission and return points awarded."""
        if mission_id in self.completed_missions:
            return None

        mission = next((m for m in self.missions if m.id == mission_id), None)
        if mission is None:
            return None

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
            timestamp=datetime.now(timezone.utc),
        )
        self.chat_history.append(chat_message)

    def get_chat_history(self) -> List[ChatMessage]:
        """Get the full chat history."""
        return self.chat_history.copy()


class SessionManager:
    """Manages per-session state and DB persistence for progress."""

    def __init__(self):
        # In-memory registry for compatibility with existing code/tests
        self.sessions: Dict[str, SessionData] = {}
        self.revoked_tokens: Set[str] = set()

    # ===== In-memory API (compat) =====
    async def create_session(self, session_id: str) -> SessionData:
        session_data = SessionData(session_id)
        self.sessions[session_id] = session_data
        return session_data

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        return self.sessions.get(session_id)

    async def revoke_token(self, token: str) -> None:
        self.revoked_tokens.add(token)

    async def is_token_revoked(self, token: str) -> bool:
        return token in self.revoked_tokens

    # ===== DB-backed helpers for SessionProgress =====
    async def get_session_progress(self, session_id: str) -> Optional[SessionProgress]:
        """Fetch `SessionProgress` from DB if it exists.

        Returns a dict shaped like `SessionProgress`, with columns stored explicitly
        in the `session_progress` table.
        """
        query = """
            SELECT session_id, goal, hero, process, missions, case_studies, 
                points_total, call_unlocked, why_this_case_studies_were_selected, why, created_at, updated_at
            FROM session_progress
            WHERE session_id = %s
        """
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (session_id,))
                row = await cur.fetchone()
                if not row:
                    return None
                progress: Dict[str, Any] = {
                    "session_id": row.get("session_id", session_id),
                    "goal": row.get("goal"),
                    "hero": row.get("hero"),
                    "process": row.get("process"),
                    "why_this_case_studies_were_selected": row.get("why_this_case_studies_were_selected"),
                    "why": row.get("why"),
                    "missions": row.get("missions"),
                    "case_studies": row.get("case_studies"),
                    "points_total": row.get("points_total"),
                    "call_unlocked": row.get("call_unlocked"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                }
                return cast(SessionProgress, progress)

    async def insert_session_progress_if_absent(self, session_id: str, progress: SessionProgress) -> bool:
        """Insert `SessionProgress` only if it does not already exist.

        Returns True if inserted, False if a record already existed.
        """
        # Normalize payload to plain JSON-serializable dict
        payload = self._normalize_progress(progress)

        query = """
            INSERT INTO session_progress (
                session_id, goal, hero, process, missions, case_studies,
                why_this_case_studies_were_selected, why, points_total, call_unlocked
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO NOTHING
        """
        values = (
            session_id,
            payload.get("goal"),
            Json(payload.get("hero")) if payload.get("hero") is not None else None,
            Json(payload.get("process")) if payload.get("process") is not None else None,
            Json(payload.get("missions")) if payload.get("missions") is not None else None,
            Json(payload.get("case_studies")) if payload.get("case_studies") is not None else None,
            payload.get("why_this_case_studies_were_selected"),
            payload.get("why"),
            payload.get("points_total"),
            payload.get("call_unlocked"),
        )

        print(f"INFO: Payload: {payload} \n Values: {values} ")
        try:
            async with transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, values)
                    # rowcount is 1 only if insert happened
                    return cur.rowcount == 1
        except Exception as exc:
            print("ERROR: insert_session_progress_if_absent failed:")
            print(f"  session_id={session_id}")
            print(f"  values={values}")
            print(f"  exception={exc}")
            traceback.print_exc()
            raise

    async def upsert_session_progress(self, session_id: str, progress: SessionProgress) -> None:
        """Insert or update `SessionProgress` in DB."""
        payload = self._normalize_progress(progress)

        query = """
            INSERT INTO session_progress (
                session_id, goal, hero, missions, case_studies,
                points_total, call_unlocked
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id)
            DO UPDATE SET
                goal = EXCLUDED.goal,
                hero = EXCLUDED.hero,
                missions = EXCLUDED.missions,
                case_studies = EXCLUDED.case_studies,
                points_total = EXCLUDED.points_total,
                call_unlocked = EXCLUDED.call_unlocked,
                updated_at = NOW()
        """
        values = (
            session_id,
            payload.get("goal"),
            Json(payload.get("hero")) if payload.get("hero") is not None else None,
            Json(payload.get("missions")) if payload.get("missions") is not None else None,
            Json(payload.get("case_studies")) if payload.get("case_studies") is not None else None,
            payload.get("points_total"),
            payload.get("call_unlocked"),
        )
        try:
            async with transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, values)
        except Exception as exc:
            print("ERROR: upsert_session_progress failed:")
            print(f"  session_id={session_id}")
            print(f"  values={values}")
            print(f"  exception={exc}")
            traceback.print_exc()
            raise

    def _normalize_progress(self, progress: SessionProgress) -> Dict[str, Any]:
        """Convert `SessionProgress` to a plain JSON-serializable dict.

        Handles Pydantic models, sets, and nested structures.
        """
        def to_plain(value: Any) -> Any:
            # Pydantic v2
            if hasattr(value, "model_dump"):
                return value.model_dump()
            if isinstance(value, list):
                return [to_plain(v) for v in value]
            if isinstance(value, set):
                return [to_plain(v) for v in value]
            if isinstance(value, dict):
                return {k: to_plain(v) for k, v in value.items()}
            return value

        return cast(Dict[str, Any], to_plain(progress))


# Global session manager instance
session_manager = SessionManager()