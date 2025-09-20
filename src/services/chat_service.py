"""Chat service for the chat endpoint."""

import logging
import time
from dataclasses import dataclass
from typing import List, Sequence

from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.models.chat import ChatResponse
from src.prompt.chat_prompt import FOLLOWUP_PROMPT, USER_MESSAGE_CONTEXT, WELCOME_PROMPT
from src.services.llm_services import get_history, llm
from src.services.session_manager import session_manager
from src.utils.errors import raise_http_error
from src.utils.json_utils import extract_json_from_fenced_block
from src.utils.llm_validation import LLMValidationError, validate_chat_payload
from src.utils.retry import CircuitBreakerOpenError, LLM_CIRCUIT_BREAKER, async_retry


logger = logging.getLogger(__name__)


@dataclass
class ChatServiceResult:
    """Result wrapper containing the API response and messages to persist."""

    response: ChatResponse
    messages_to_persist: Sequence[BaseMessage]


class ChatService:
    """Handles chat interaction with the LLM."""

    async def init_chat(self, *, session_id: str, page: str, section: str):
        """Initialize a chat session."""
        progress = await session_manager.get_session_progress(session_id) or {}
        history = await get_history(session_id)
        messages = await history.aget_messages()

        if len(messages) <= 1:
            raise_http_error(404, "Session does not have a goal")

        prompt_template = ChatPromptTemplate.from_messages([("system", WELCOME_PROMPT)])

        sys_prompt = prompt_template.format(
            page=page,
            section=section,
            progress_json=progress.get("missions", []),
        )

        messages.append(SystemMessage(content=sys_prompt))

        try:
            llm_response = await llm.ainvoke(messages)
            response = llm_response.content
            return response
        except Exception as exc:  # pragma: no cover - pass through existing error path
            logger.error("LLM Parse Error during init chat: %s", exc, exc_info=True)
            raise_http_error(500, "AI assistant temporarily unavailable")

    async def ask(self, *, session_id: str, message: str, page: str, section: str) -> ChatServiceResult:
        """Generate a response to an ask message."""
        if not message or not message.strip():
            raise_http_error(400, "Message cannot be empty")

        progress = await session_manager.get_session_progress(session_id) or {}
        history = await get_history(session_id)
        existing_messages = await history.aget_messages()

        if len(existing_messages) <= 1:
            raise_http_error(404, "Session does not have a goal")

        start_time = time.perf_counter()
        session_logger = logging.LoggerAdapter(
            logger,
            {"session_id": session_id, "page": page, "section": section},
        )

        session_logger.info(
            "ChatService ask invoked",
            extra={"event": "chat.service.ask", "stage": "start"},
        )

        conversation: List[BaseMessage] = list(existing_messages)
        new_messages: List[BaseMessage] = []

        if len(existing_messages) == 5:
            session_logger.info(
                "Adding follow-up system prompt",
                extra={"event": "chat.service.ask", "stage": "followup_prompt"},
            )
            follow_up_message = SystemMessage(content=FOLLOWUP_PROMPT)
            conversation.append(follow_up_message)
            new_messages.append(follow_up_message)

        context_template = ChatPromptTemplate.from_messages([("system", USER_MESSAGE_CONTEXT)])
        context_messages = context_template.format_messages(
            page=page,
            section=section,
            progress_json=progress.get("missions", []),
        )
        conversation.extend(context_messages)
        new_messages.extend(context_messages)

        user_message_template = ChatPromptTemplate.from_messages([("user", """{user_input}""")])
        user_messages = user_message_template.format_messages(user_input=message)
        conversation.extend(user_messages)
        new_messages.extend(user_messages)

        async def invoke_llm():
            return await llm.ainvoke(conversation)

        try:
            llm_response = await async_retry(
                invoke_llm,
                operation_name="chat_llm_invoke",
                logger=session_logger,
                max_attempts=3,
                base_delay=0.75,
                max_delay=6.0,
                multiplier=2.0,
                jitter=0.35,
                circuit_breaker=LLM_CIRCUIT_BREAKER,
                breaker_key="llm:chat",
            )
            response_content = llm_response.content
        except CircuitBreakerOpenError as breaker_exc:
            session_logger.warning(
                "Chat LLM circuit breaker open",
                extra={
                    "event": "chat.service.ask",
                    "stage": "circuit_open",
                    "retry_after": round(breaker_exc.retry_after, 2),
                },
            )
            raise_http_error(503, "AI assistant temporarily unavailable")
        except Exception:
            session_logger.error(
                "LLM interaction failed",
                extra={"event": "chat.service.ask", "stage": "llm_invoke"},
                exc_info=True,
            )
            raise_http_error(502, "AI assistant temporarily unavailable")

        try:
            json_response = extract_json_from_fenced_block(response_content)
            # Validate the parsed response structure
            validate_chat_payload(json_response)
        except ValueError as exc:
            session_logger.error(
                "Failed to parse LLM response",
                extra={"event": "chat.service.ask", "stage": "json_parse"},
                exc_info=True,
            )
            raise LLMValidationError(
                "Invalid response format from AI service",
                "CHAT_INVALID_JSON",
                "retry_or_new_message"
            )
        except LLMValidationError as validation_error:
            session_logger.error(
                "Chat payload validation failed",
                extra={
                    "event": "chat.service.ask",
                    "stage": "payload_validation",
                    "error_code": validation_error.error_code,
                },
            )
            raise validation_error

        reply = json_response.get("reply")
        if not reply:
            session_logger.error(
                "LLM response missing reply",
                extra={"event": "chat.service.ask", "stage": "missing_reply"},
            )
            raise LLMValidationError(
                "AI assistant response incomplete",
                "CHAT_MISSING_REPLY",
                "retry_or_new_message"
            )

        ai_message = AIMessage(content=response_content)
        new_messages.append(ai_message)

        projected_history = list(existing_messages) + new_messages
        message_history = self._build_history(projected_history)

        navigate = json_response.get("navigate") or {}

        response_model = ChatResponse(
            reply=reply,
            history=message_history[:-2] if len(message_history) >= 2 else [],
            updatedProgress={
                "pointsTotal": progress.get("points_total"),
                "missions": progress.get("missions"),
                "callUnlocked": progress.get("call_unlocked"),
            },
            followUpMissions=json_response.get("followUpMissions"),
            suggestedRead=[],
            navigate=navigate,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        session_logger.info(
            "ChatService ask completed",
            extra={
                "event": "chat.service.ask",
                "stage": "complete",
                "duration_ms": round(duration_ms, 2),
            },
        )

        return ChatServiceResult(response=response_model, messages_to_persist=new_messages)

    @staticmethod
    def _build_history(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
        """Convert stored messages into plain user/assistant history."""
        message_history: List[BaseMessage] = []

        for stored in messages[6:]:
            if stored.type == "system":
                continue
            if stored.type == "ai":
                reply = None
                content = stored.content
                if isinstance(content, str):
                    try:
                        payload = extract_json_from_fenced_block(content)
                        reply = payload.get("reply")
                    except ValueError:
                        reply = None
                if reply:
                    message_history.append(AIMessage(content=reply))
            elif stored.type == "human":
                message_history.append(HumanMessage(content=stored.content))

        return message_history


chat_service = ChatService()
