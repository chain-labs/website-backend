"""Utility helpers for chat history persistence with rollback support."""

import logging
from typing import Iterable, List

from langchain_core.messages import BaseMessage

from src.database import get_connection
from src.services.llm_services import get_history

logger = logging.getLogger(__name__)


async def append_history_messages(session_id: str, messages: Iterable[BaseMessage]) -> None:
    """Persist a sequence of messages for a session."""
    message_list: List[BaseMessage] = list(messages)
    if not message_list:
        return

    history = await get_history(session_id)
    await history.aadd_messages(message_list)


async def rollback_last_messages(session_id: str, count: int) -> None:
    """Remove the most recent ``count`` messages for the session.

    Used as a best-effort rollback when a response cannot be delivered after
    the LLM output has already been written to the message store.
    """
    if count <= 0:
        return

    delete_query = """
        DELETE FROM message_store
        WHERE id IN (
            SELECT id FROM message_store
            WHERE session_id = %s
            ORDER BY id DESC
            LIMIT %s
        )
    """

    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(delete_query, (session_id, count))
    except Exception as exc:  # pragma: no cover - best-effort cleanup
        logger.warning("Failed to rollback chat history for session %s: %s", session_id, exc)
