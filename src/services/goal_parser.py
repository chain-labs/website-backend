import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable vector store
os.environ["LITELLM_DISABLE_VECTOR_STORE"] = "true"
os.environ['LITELLM_LOG'] = 'DEBUG'

# from langchain_litellm import ChatLiteLLM
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from ..utils.errors import raise_http_error
from src.services.llm_services import get_history, llm
from ..prompt.goal_prompt import goalPromptTemplate, template_prompt
from ..utils.retry import (
    CircuitBreakerOpenError,
    LLM_CIRCUIT_BREAKER,
    async_retry,
)


@dataclass
class ParsedLLMResult:
    """Structured result containing model output and history messages."""

    content: Any
    messages_to_persist: List[BaseMessage]
    raw_response: Optional[Dict[str, Any]] = None


async def parse_user_goal(user_prompt: str, session_id: str) -> ParsedLLMResult:
    """
    Parse user goal using LLM and return structured response.
    
    Args:
        prompt: List of BaseMessage objects containing the prompt
        
    Returns:
        dict: Parsed goal response
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        session_logger = logging.LoggerAdapter(logger, {"session_id": session_id})

        history = await get_history(session_id)
        messages = await history.aget_messages()

        if (len(messages) != 0):
            raise_http_error(400, "Session already has a goal")

        session_logger.info(
            "Invoking LLM for goal parsing",
            extra={"event": "goal_parser.invoke.start"}
        )

        session_logger.debug(
            "Goal prompt prepared",
            extra={"event": "goal_parser.prompt", "prompt_preview": user_prompt[:200]}
        )


        base_chain = goalPromptTemplate | llm

        async def invoke_llm():
            return await base_chain.ainvoke({"user_goal_input": user_prompt})

        try:
            raw_response = await async_retry(
                invoke_llm,
                operation_name="goal_llm_invoke",
                logger=session_logger,
                max_attempts=3,
                base_delay=0.75,
                max_delay=6.0,
                multiplier=2.0,
                jitter=0.35,
                circuit_breaker=LLM_CIRCUIT_BREAKER,
                breaker_key="llm:goal",
            )
        except CircuitBreakerOpenError as breaker_exc:
            session_logger.warning(
                "Goal LLM circuit breaker open",
                extra={
                    "event": "goal_parser.circuit_open",
                    "retry_after": round(breaker_exc.retry_after, 2),
                }
            )
            raise_http_error(503, "AI service temporarily unavailable. Please try again later.")

        session_logger.info(
            "Received response from LLM",
            extra={"event": "goal_parser.invoke.success"}
        )

        # Log the raw response for debugging
        session_logger.debug(
            "Raw response received",
            extra={"event": "goal_parser.response.raw", "response_preview": str(raw_response)[:200]}
        )

        # Parse the response
        try:
            response_content = json.loads(raw_response.content)
            session_logger.debug(
                "Response content extracted",
                extra={
                    "event": "goal_parser.response.content",
                    "content_preview": json.dumps(response_content)[:200],
                }
            )

            clarification_question = response_content.get("clarificationQuestion")
            if isinstance(clarification_question, str):
                clarification_question = clarification_question.strip()
            else:
                clarification_question = ""

            history_messages = [
                SystemMessage(content=template_prompt),
                HumanMessage(content=user_prompt),
                AIMessage(content=clarification_question),
            ]

            return ParsedLLMResult(
                content=clarification_question,
                messages_to_persist=history_messages,
                raw_response=response_content,
            )
        except json.JSONDecodeError as je:
            session_logger.error(
                "Failed to parse JSON response",
                extra={"event": "goal_parser.response.invalid_json"},
                exc_info=True,
            )
            raise_http_error(500, "Invalid response format from AI service")

    except Exception as e:
        session_logger = logging.LoggerAdapter(logger, {"session_id": session_id})
        session_logger.error(
            "Error in parse_user_goal",
            extra={"event": "goal_parser.failure"},
            exc_info=True,
        )
        raise_http_error(
            500, 
            f"Error processing your request: {str(e)}. Please try again later."
        )


async def parse_user_clarification(user_prompt: str, session_id: str) -> ParsedLLMResult:
    session_logger = logging.LoggerAdapter(logger, {"session_id": session_id})

    history = await get_history(session_id)

    messages = await history.aget_messages()

    # print(f"Messages: {messages}")

    if len(messages) == 0:
        raise_http_error(404, "No chat history found for session")
    if len(messages) > 3:
        raise_http_error(400, "Session already has a clarification")

    try:
        messages.append(HumanMessage(content=user_prompt))

        async def invoke_llm():
            return await llm.ainvoke(messages)

        try:
            response = await async_retry(
                invoke_llm,
                operation_name="clarify_llm_invoke",
                logger=session_logger,
                max_attempts=3,
                base_delay=0.75,
                max_delay=6.0,
                multiplier=2.0,
                jitter=0.35,
                circuit_breaker=LLM_CIRCUIT_BREAKER,
                breaker_key="llm:clarify",
            )
        except CircuitBreakerOpenError as breaker_exc:
            session_logger.warning(
                "Clarify LLM circuit breaker open",
                extra={
                    "event": "goal_parser.clarify.circuit_open",
                    "retry_after": round(breaker_exc.retry_after, 2),
                }
            )
            raise_http_error(503, "AI service temporarily unavailable. Please try again later.")

        raw_content = response.content
        if isinstance(raw_content, str):
            raw_content_str = raw_content.strip()
        else:
            raw_content_str = json.dumps(raw_content)

        try:
            response_payload = json.loads(raw_content_str)
            session_logger.debug(
                "Clarify response extracted",
                extra={
                    "event": "goal_parser.clarify.response",
                    "content_preview": json.dumps(response_payload)[:200],
                }
            )
        except json.JSONDecodeError:
            session_logger.error(
                "Clarify response not valid JSON",
                extra={"event": "goal_parser.clarify.invalid_json"},
                exc_info=True,
            )
            raise_http_error(500, "Invalid clarification response format from AI service")

        ai_message_content = raw_content_str
        if isinstance(response_payload, dict):
            personalized_pitch = response_payload.get("personalizedPitch")
            if isinstance(personalized_pitch, (dict, list)):
                ai_message_content = json.dumps(personalized_pitch)

        history_messages = [
            HumanMessage(content=user_prompt),
            AIMessage(content=ai_message_content),
        ]

        return ParsedLLMResult(
            content=response_payload,
            messages_to_persist=history_messages,
            raw_response=response_payload,
        )

    except Exception as e:
        session_logger.error(
            "Error while clarifying goal",
            extra={"event": "goal_parser.clarify.failure"},
            exc_info=True,
        )
        raise_http_error(500, f"Failed to clarify goal: {str(e)}")
