"""Chat endpoint routes."""

import json
import logging
import time
from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.utils.json_utils import FENCED_JSON_PATTERN, extract_json_from_fenced_block

from ..models.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from ..auth.middleware import get_current_session
from ..services.session_manager import session_manager
from ..services.chat_service import chat_service
from ..services.history_manager import append_history_messages, rollback_last_messages
from ..utils.errors import raise_http_error, raise_structured_error
from ..utils.llm_validation import LLMValidationError, validate_chat_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    chat_request: ChatRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Continue contextual conversation with the AI assistant.
    
    **Description:**
    This endpoint enables ongoing conversation with the AI assistant once the 
    personalized micro-site is live. The assistant maintains full context about
    the user's progress, current page, and goals to provide relevant guidance.
    
    **When to use:**
    - When users need guidance on their AI agent project
    - For contextual help based on current page/section
    - To get mission recommendations and next steps
    - When users ask questions about their progress
    - For getting personalized advice and navigation guidance
    
    **Request Body:**
    ```json
    {
      "message": "Which mission should I tackle next?",
      "context": {
        "page": "mission-dashboard",
        "section": "mission-1",
        "metadata": { "missionId": "defineMetrics" }
      }
    }
    ```
    
    **Context Parameters:**
    - **page**: Current page identifier (e.g., "micro-landing", "case-study", "mission-dashboard")
    - **section**: Specific section/component (e.g., "hero", "mission-3", "progress-widget")  
    - **metadata**: Optional extra state like mission or case study IDs
    
    **Response Example:**
    ```json
    {
      "reply": "Great—you've completed defining your metrics. Next, sketch the agent's decision flow.",
      "history": [
        { "role": "user", "message": "Done with metrics.", "timestamp": "2025-01-20T10:00:10Z" },
        { "role": "assistant", "message": "Next, sketch the decision flow...", "timestamp": "2025-01-20T10:00:12Z" }
      ],
      "updatedProgress": {
        "pointsTotal": 15,
        "missions": [
          { "id": "defineMetrics", "status": "completed", "points": 15 },
          { "id": "sketchFlow", "status": "pending", "points": 15 }
        ],
        "callUnlocked": false
      },
      "followUpMissions": [
        { "id": "sketchFlow", "title": "Sketch Agent Flow", "points": 15 }
      ],
      "suggestedRead": [
        { "id": "cs2", "title": "Menu Recommender", "summary": "How we boosted upsell by 22%" }
      ],
      "navigate": {
        "page": "mission-dashboard",
        "section": "mission-2", 
        "metadata": { "missionId": "sketchFlow" }
      }
    }
    ```
    
    **Response Features:**
    - **reply**: Contextual AI response based on message and current location
    - **history**: Complete chat conversation history
    - **updatedProgress**: Current mission status and points (when relevant)
    - **followUpMissions**: New missions to work on (when applicable)
    - **suggestedRead**: Recommended case studies (when helpful)
    - **navigate**: Frontend routing instruction (when appropriate)
    
    **Usage Examples:**
    
    **Get Mission Guidance:**
    ```javascript
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: "I'm stuck on defining metrics. What should I focus on?",
        context: {
          page: "mission-dashboard",
          section: "mission-1",
          metadata: { missionId: "defineMetrics" }
        }
      })
    });
    ```
    
    **Ask for Progress Update:**
    ```javascript
    const response = await fetch('/api/chat', {
      method: 'POST', 
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: "How many points have I earned so far?",
        context: {
          page: "mission-dashboard",
          section: "progress-widget"
        }
      })
    });
    ```
    
    **Get Case Study Recommendations:**
    ```javascript
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: "Can you show me examples similar to my project?", 
        context: {
          page: "micro-landing",
          section: "hero"
        }
      })
    });
    ```
    
    **Error Cases:**
    - **400 Bad Request**: Missing or invalid message/context fields
      ```json
      { "error": { "code": 400, "message": "Message cannot be empty" } }
      ```
    - **401 Unauthorized**: Missing or invalid access token
      ```json
      { "error": { "code": 401, "message": "Invalid token" } }
      ```
    - **404 Not Found**: Session not found (rare, indicates token/session mismatch)
      ```json
      { "error": { "code": 404, "message": "Session not found" } }
      ```
    - **500 Internal Server Error**: AI assistant or backend failure
      ```json
      { "error": { "code": 500, "message": "AI assistant temporarily unavailable" } }
      ```
    
    **Notes:**
    - Chat history is maintained server-side and returned in each response
    - The assistant uses context to provide relevant, personalized guidance
    - Optional response fields (followUpMissions, navigate, etc.) depend on message content
    - Navigation instructions help frontend show the most relevant page/section
    - All timestamps are in UTC ISO format
    """
    start_time = time.perf_counter()
    logger.info(
        "Processing chat request",
        extra={
            "session_id": session_id,
            "event": "chat.ask.start",
            "page": chat_request.context.page,
            "section": chat_request.context.section,
        }
    )

    try:
        service_result = await chat_service.ask(
            session_id=session_id,
            message=chat_request.message,
            page=chat_request.context.page,
            section=chat_request.context.section,
        )

        history_messages = list(service_result.messages_to_persist)

        try:
            await append_history_messages(session_id, history_messages)
        except Exception as storage_error:
            logger.exception(
                "Chat history persistence failed",
                extra={
                    "session_id": session_id,
                    "event": "chat.ask.history_failure",
                    "messages_to_persist": len(history_messages),
                }
            )
            await rollback_last_messages(session_id, len(history_messages))
            raise_structured_error(500, "Failed to persist chat history", "DATABASE_FAILURE", "retry_or_new_message")

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Chat response generated",
            extra={
                "session_id": session_id,
                "event": "chat.ask.success",
                "duration_ms": round(duration_ms, 2),
            }
        )

        return service_result.response
    except LLMValidationError as validation_error:
        # Re-raise validation errors from chat service
        logger.warning(
            "Chat payload validation failed",
            extra={
                "session_id": session_id,
                "event": "chat.ask.validation_failed",
                "error_code": validation_error.error_code,
            }
        )
        raise_structured_error(
            422,
            validation_error.args[0],
            validation_error.error_code,
            validation_error.retry_action
        )
    except Exception as e:
        logger.exception(
            "Unhandled exception during chat request",
            extra={
                "session_id": session_id,
                "event": "chat.ask.unhandled_exception",
            }
        )
        if hasattr(e, "status_code"):
            raise e

        # Check if it's a timeout or rate limit error
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["timeout", "rate limit", "429", "503"]):
            logger.warning(
                "AI service overloaded during chat request",
                extra={
                    "session_id": session_id,
                    "event": "chat.ask.overloaded",
                }
            )
            raise_structured_error(502, "AI assistant temporarily overloaded", "CHAT_SERVICE_OVERLOADED", "retry_or_new_message")
        else:
            logger.error(
                "Chat response generation failed",
                extra={
                    "session_id": session_id,
                    "event": "chat.ask.failure",
                }
            )
            raise_structured_error(500, "Failed to generate response", "CHAT_RESPONSE_FAILED", "retry_or_new_message")


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str = Depends(get_current_session)):
    """Return the persisted chat history for the authenticated session."""

    logger.info(
        "Fetching chat history",
        extra={
            "session_id": session_id,
            "event": "chat.history.fetch",
        }
    )

    try:
        history_messages = await chat_service.get_chat_history(session_id=session_id)
        return ChatHistoryResponse(history=history_messages)
    except Exception:
        logger.exception(
            "Failed to fetch chat history",
            extra={
                "session_id": session_id,
                "event": "chat.history.failure",
            }
        )
        raise_structured_error(500, "Failed to fetch chat history", "CHAT_HISTORY_FETCH_FAILED", "retry_or_new_message")
