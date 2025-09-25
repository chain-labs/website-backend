"""Session management utilities.

This module provides two layers:
- A lightweight in-memory API (`SessionData`, `SessionManager.create_session`, etc.) that existing
  code and tests rely on.
- DB-backed helpers to persist and retrieve `SessionProgress` for long-lived session state.
"""

from typing import Any, Dict, List, Optional, Set, cast
import logging
from psycopg.types.json import Json
from datetime import datetime, timezone

from src.utils.errors import raise_http_error

from ..models.goal import Goal, Mission, CaseStudy
from ..models.mission import MissionStatus
from ..models.chat import ChatMessage
from ..models.db.db_models import SessionProgress
from ..database import get_connection, transaction


logger = logging.getLogger(__name__)


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
        logger.debug(
            "Fetching session progress from database",
            extra={
                "session_id": session_id,
                "event": "session_progress.fetch.start",
            }
        )

        query = """
            SELECT session_id, goal, hero, process, missions, case_studies, 
                points_total, call_unlocked, call_record, why_this_case_studies_were_selected, why, created_at, updated_at
            FROM session_progress
            WHERE session_id = %s
        """

        logger.debug(
            "Executing session progress query",
            extra={
                "session_id": session_id,
                "event": "session_progress.fetch.query",
            }
        )

        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (session_id,))
                row = await cur.fetchone()
                logger.debug(
                    "Session progress query completed",
                    extra={
                        "session_id": session_id,
                        "event": "session_progress.fetch.result",
                        "row_found": row is not None,
                    }
                )

                if not row:
                    logger.debug(
                        "No session progress record found",
                        extra={
                            "session_id": session_id,
                            "event": "session_progress.fetch.not_found",
                        }
                    )
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
                    "call_record": row.get("call_record", []),
                }
                return cast(SessionProgress, progress)

    async def get_or_create_session_from_db(self, session_id: str) -> Optional[SessionData]:
        """Get session from DB and load it into memory, or return existing in-memory session.
        
        This method ensures we have a SessionData object with all the necessary methods
        for mission completion, regardless of whether the data came from DB or memory.
        """
        logger.debug(
            "Loading session from memory or database",
            extra={
                "session_id": session_id,
                "event": "session.load.start",
            }
        )

        # First check if we already have it in memory
        if session_id in self.sessions:
            logger.debug(
                "Session found in memory",
                extra={
                    "session_id": session_id,
                    "event": "session.load.memory_hit",
                }
            )
            # Check if the in-memory session has missions, if not, reload from DB
            existing_session = self.sessions[session_id]
            if not existing_session.missions:
                logger.debug(
                    "In-memory session missing missions, reloading",
                    extra={
                        "session_id": session_id,
                        "event": "session.load.memory_reload",
                    }
                )
                # Remove from memory to force reload from DB
                del self.sessions[session_id]
            else:
                logger.debug(
                    "Using in-memory session",
                    extra={
                        "session_id": session_id,
                        "event": "session.load.memory_use",
                        "mission_count": len(existing_session.missions),
                    }
                )
                return existing_session

        logger.debug(
            "Session not in memory - loading from database",
            extra={
                "session_id": session_id,
                "event": "session.load.db_lookup",
            }
        )
        
        # Try to get from database
        progress = await self.get_session_progress(session_id)
        logger.debug(
            "Database progress lookup completed",
            extra={
                "session_id": session_id,
                "event": "session.load.db_result",
                "progress_found": progress is not None,
            }
        )

        if not progress:
            logger.debug(
                "No session progress found in database",
                extra={
                    "session_id": session_id,
                    "event": "session.load.db_not_found",
                }
            )
            return None
        
        # Create a new SessionData object from the database data
        session_data = SessionData(session_id)
        
        # Load the data from the database
        if progress.get("goal"):
            session_data.goal = progress["goal"]
        if progress.get("missions"):
            # Convert dict missions to Mission objects
            missions = progress["missions"]
            if missions and isinstance(missions[0], dict):
                # Convert dict missions to Mission objects
                from ..models.goal import Mission
                session_data.missions = [
                    Mission(
                        id=mission["id"],
                        title=mission.get("title", ""),
                        category=mission.get("category", ""),
                        points=mission.get("points", 0),
                        status=mission.get("status", "pending")
                    )
                    for mission in missions
                ]
            else:
                session_data.missions = missions
        if progress.get("points_total") is not None:
            session_data.points_total = progress["points_total"]
        # Reconstruct completed_missions from mission statuses
        if progress.get("missions"):
            missions = progress["missions"]
            if missions and isinstance(missions[0], dict):
                # Extract completed mission IDs from mission statuses
                completed_ids = {
                    mission["id"] 
                    for mission in missions 
                    if mission.get("status") == "completed"
                }
                session_data.completed_missions = completed_ids
        
        # Store in memory for future use
        self.sessions[session_id] = session_data
        return session_data

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

        logger.debug(
            "Attempting to insert session progress if absent",
            extra={
                "session_id": session_id,
                "event": "session_progress.insert_if_absent",
                "has_missions": bool(payload.get("missions")),
            }
        )
        try:
            async with transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, values)
                    # rowcount is 1 only if insert happened
                    return cur.rowcount == 1
        except Exception as exc:
            logger.exception(
                "Failed to insert session progress",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.insert_if_absent.error",
                }
            )
            raise

    async def upsert_session_progress(self, session_id: str, progress: SessionProgress) -> None:
        """Insert or update `SessionProgress` in DB."""
        payload = self._normalize_progress(progress)

        query = """
            INSERT INTO session_progress (
                session_id, goal, hero, process, missions, case_studies,
                why_this_case_studies_were_selected, why, points_total, call_unlocked, call_record
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id)
            DO UPDATE SET
                goal = EXCLUDED.goal,
                hero = EXCLUDED.hero,
                process = EXCLUDED.process,
                missions = EXCLUDED.missions,
                case_studies = EXCLUDED.case_studies,
                why_this_case_studies_were_selected = EXCLUDED.why_this_case_studies_were_selected,
                why = EXCLUDED.why,
                points_total = EXCLUDED.points_total,
                call_unlocked = EXCLUDED.call_unlocked,
                call_record = EXCLUDED.call_record,
                updated_at = NOW()
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
            Json(payload.get("call_record", []))
        )
        try:
            async with transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, values)
        except Exception as exc:
            logger.exception(
                "Failed to upsert session progress",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.upsert.error",
                }
            )
            raise

    async def update_mission_status(self, session_id: str, mission_id: str, status: str, points_total: int, artifact_answer: Optional[str] = None) -> None:
        """Update a specific mission's status and points total in the database."""
        try:
            logger.debug(
                "Updating mission status in persistence layer",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.mission.update",
                    "mission_id": mission_id,
                    "status": status,
                    "points_total": points_total,
                }
            )
            # First, get the current progress
            current_progress = await self.get_session_progress(session_id)
            if not current_progress:
                raise ValueError(f"No progress found for session {session_id}")
            
            # Update the specific mission status
            missions = current_progress.get("missions", [])
            updated_missions = []
            
            for mission in missions:
                if mission.get("id") == mission_id:
                    # Update this mission's status
                    updated_mission = mission.copy()
                    updated_mission["status"] = status
                    # Optionally persist the artifact answer for this mission
                    if artifact_answer is not None and str(artifact_answer).strip() != "":
                        updated_mission["artifact"] = {"answer": artifact_answer}
                    updated_missions.append(updated_mission)
                else:
                    updated_missions.append(mission)
            
            # Update the progress with new missions and points
            updated_progress = current_progress.copy()
            updated_progress["missions"] = updated_missions
            updated_progress["points_total"] = points_total
            updated_progress["call_unlocked"] = points_total >= 50  # Simple unlock logic
            
            # Save the updated progress
            await self.upsert_session_progress(session_id, updated_progress)
            logger.debug(
                "Mission status persisted",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.mission.update.success",
                    "mission_id": mission_id,
                }
            )
        except Exception as exc:
            logger.exception(
                "Failed to update mission status",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.mission.update.error",
                    "mission_id": mission_id,
                }
            )
            raise

    async def store_call_record(self, session_id: str, uid: str, id: str):
        """Add booked call record to the session data"""

        try:
            current_progress = await self.get_session_progress(session_id)
            logger.debug(
                "Storing call record for session",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.call_record.start",
                    "call_id": id,
                }
            )

            if not current_progress:
                raise ValueError(f"No progress found for session {session_id}")

            updated_progress = current_progress.copy()
            current_call_record = current_progress.get("call_record", [])

            current_call_record.append({
                "id": id,
                "uid": uid
            })

            updated_progress["call_record"] = current_call_record

            await self.upsert_session_progress(session_id, updated_progress)
            logger.debug(
                "Call record stored",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.call_record.success",
                    "calls_recorded": len(current_call_record),
                }
            )

        except ValueError as e:
            logger.warning(
                "Session progress missing while storing call record",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.call_record.missing_progress",
                }
            )
            raise_http_error(400, "No progress found for current session")
        except Exception as e:
            logger.exception(
                "Failed to store call record",
                extra={
                    "session_id": session_id,
                    "event": "session_progress.call_record.error",
                }
            )
            raise_http_error(500, "Something went wrong while storing call_record")


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
