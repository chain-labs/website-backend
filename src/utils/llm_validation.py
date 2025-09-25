"""LLM response validation utilities for CHA-110 error handling."""

import json
import logging
from typing import Any, Dict, Optional, List
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


class LLMValidationError(Exception):
    """Exception raised when LLM response validation fails."""

    def __init__(self, message: str, error_code: str, retry_action: str):
        super().__init__(message)
        self.error_code = error_code
        self.retry_action = retry_action


def validate_clarify_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate /clarify LLM response payload before persisting to session state.

    Raises LLMValidationError if validation fails with appropriate error codes.
    """
    if not isinstance(payload, dict):
        raise LLMValidationError(
            "Invalid response format from AI service",
            "CLARIFY_INVALID_PAYLOAD",
            "retry_or_restart"
        )

    is_valid = payload.get("isValidClarification")
    if is_valid is not True:
        error_message = payload.get("errorMessage")
        if not isinstance(error_message, str) or not error_message.strip():
            error_message = "Clarification did not meet the required specificity."

        raise LLMValidationError(
            error_message,
            "CLARIFY_INVALID",
            "retry",
        )

    pitch_payload = payload.get("personalizedPitch")

    if isinstance(pitch_payload, str):
        try:
            pitch_payload = json.loads(pitch_payload)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode personalized pitch JSON", exc_info=True)
            raise LLMValidationError(
                "Invalid personalized pitch format from AI service",
                "CLARIFY_INVALID_PITCH",
                "retry_or_restart"
            ) from exc

    if not isinstance(pitch_payload, dict):
        raise LLMValidationError(
            "Clarification response missing personalized pitch",
            "CLARIFY_MISSING_PITCH",
            "retry_or_restart"
        )

    # Check for required sections inside personalized pitch
    required_fields = ["hero", "process", "missions"]
    missing_fields = [field for field in required_fields if not pitch_payload.get(field)]

    if missing_fields:
        logger.error(f"Clarify payload missing required fields: {missing_fields}")
        raise LLMValidationError(
            f"Incomplete AI response - missing: {', '.join(missing_fields)}",
            "CLARIFY_INCOMPLETE_RESPONSE",
            "retry_or_restart"
        )

    # Validate hero structure
    hero = pitch_payload.get("hero", {})
    if not isinstance(hero, dict) or not hero.get("title") or not hero.get("description"):
        raise LLMValidationError(
            "Invalid hero section in AI response",
            "CLARIFY_INVALID_HERO",
            "retry_or_restart"
        )

    # Validate process structure
    process = pitch_payload.get("process", [])
    if not isinstance(process, list) or len(process) == 0:
        raise LLMValidationError(
            "Invalid or empty process section in AI response",
            "CLARIFY_INVALID_PROCESS",
            "retry_or_restart"
        )

    # Validate missions structure
    missions = pitch_payload.get("missions", [])
    if not isinstance(missions, list) or len(missions) == 0:
        raise LLMValidationError(
            "Invalid or empty missions section in AI response",
            "CLARIFY_INVALID_MISSIONS",
            "retry_or_restart"
        )

    # Validate each mission has required fields
    for i, mission in enumerate(missions):
        if not isinstance(mission, dict):
            raise LLMValidationError(
                f"Mission {i+1} has invalid format",
                "CLARIFY_INVALID_MISSION_FORMAT",
                "retry_or_restart"
            )

        required_mission_fields = ["id", "title", "points"]
        missing_mission_fields = [field for field in required_mission_fields if not mission.get(field)]

        if missing_mission_fields:
            raise LLMValidationError(
                f"Mission {i+1} missing required fields: {', '.join(missing_mission_fields)}",
                "CLARIFY_INCOMPLETE_MISSION",
                "retry_or_restart"
            )

    return pitch_payload


def validate_goal_payload(payload: Optional[Dict[str, Any]]) -> None:
    """
    Validate /goal LLM response payload.

    For goal endpoint, we mainly validate that we got a response.
    """
    if not payload:
        raise LLMValidationError(
            "Empty response from AI service",
            "GOAL_EMPTY_RESPONSE",
            "restart_or_retry"
        )

    if not isinstance(payload, dict):
        raise LLMValidationError(
            "Invalid response format from AI service",
            "GOAL_INVALID_RESPONSE",
            "restart_or_retry",
        )

    is_valid_goal = payload.get("isValidGoal")
    if is_valid_goal is not True:
        error_message = payload.get("errorMessage")
        if not isinstance(error_message, str) or not error_message.strip():
            error_message = "Goal did not meet minimum specificity requirements."

        raise LLMValidationError(
            error_message,
            "GOAL_INVALID",
            "retry",
        )

    clarification_question = payload.get("clarificationQuestion")
    if not isinstance(clarification_question, str) or not clarification_question.strip():
        raise LLMValidationError(
            "AI response missing clarification question",
            "GOAL_MISSING_CLARIFICATION",
            "restart_or_retry",
        )


def validate_chat_payload(payload: Dict[str, Any]) -> None:
    """
    Validate /chat LLM response payload.

    Chat responses must have a 'reply' field at minimum.
    """

    logger.debug(
        "Validating chat payload",
        extra={
            "event": "chat.validation.payload",
            "payload_keys": list(payload.keys()) if isinstance(payload, dict) else None,
        }
    )

    if not payload.get('reply'):
        raise LLMValidationError(
            "AI response missing reply content",
            "CHAT_MISSING_REPLY",
            "retry_or_new_message"
        )
    

def validate_session_state_for_clarify(messages: List[BaseMessage]) -> None:
    """
    Validate that session has proper goal state and no existing clarification.

    This replaces fragile message counting with content-based validation.
    """
    if len(messages) == 0:
        raise LLMValidationError(
            "No goal found in session - please submit a goal first",
            "CLARIFY_NO_GOAL",
            "restart_or_retry"
        )

    # Check for existing goal (system message + user message + AI response pattern)
    has_goal = False
    has_clarification = False

    # Look for goal pattern: SystemMessage -> HumanMessage -> AIMessage
    for i in range(len(messages) - 2):
        if (messages[i].type == "system" and
            messages[i+1].type == "human" and
            messages[i+2].type == "ai"):
            has_goal = True
            break

    if not has_goal:
        raise LLMValidationError(
            "Invalid session state - no complete goal found",
            "CLARIFY_INVALID_SESSION",
            "restart_or_retry"
        )

    # Check for existing clarification by looking for clarification patterns
    # After goal (3 messages), if we have more messages, check if it's a clarification
    if len(messages) > 3:
        # Look for clarification pattern after goal
        for i in range(3, len(messages) - 1):
            if (messages[i].type == "human" and
                messages[i+1].type == "ai"):
                # Check if AI response looks like a clarification (contains JSON with hero/process/missions)
                ai_content = messages[i+1].content
                if isinstance(ai_content, str):
                    # Simple heuristic: clarification responses contain structured JSON
                    if any(keyword in ai_content.lower() for keyword in ['"hero"', '"process"', '"missions"']):
                        has_clarification = True
                        break

    if has_clarification:
        raise LLMValidationError(
            "Session already has a clarification - cannot clarify again",
            "CLARIFY_ALREADY_EXISTS",
            "restart_or_retry"
        )
