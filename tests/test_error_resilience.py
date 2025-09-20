"""Integration-style tests for CHA-110 error handling and retry logic."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.models.chat import ChatResponse
from src.services.chat_service import ChatServiceResult, chat_service
from src.services.goal_parser import parse_user_goal
from src.utils.retry import LLM_CIRCUIT_BREAKER, CircuitBreakerOpenError


@pytest.fixture(autouse=True)
def reset_llm_breaker():
    """Reset the shared LLM circuit breaker between tests."""
    for key in ("llm:goal", "llm:clarify", "llm:chat"):
        LLM_CIRCUIT_BREAKER.reset(key)
    yield
    for key in ("llm:goal", "llm:clarify", "llm:chat"):
        LLM_CIRCUIT_BREAKER.reset(key)


@pytest.fixture
def no_retry_delay(monkeypatch):
    """Eliminate async retry delays for deterministic and fast tests."""
    async def immediate_sleep(_):
        return None

    monkeypatch.setattr("src.utils.retry.asyncio.sleep", immediate_sleep)
    monkeypatch.setattr("src.utils.retry.random.uniform", lambda _a, _b: 0)


@pytest.mark.asyncio
async def test_chat_service_retry_recovers(monkeypatch, no_retry_delay):
    """Chat service should retry transient LLM failures and eventually succeed."""

    class DummySessionManager:
        async def get_session_progress(self, _session_id):
            return {"missions": [], "points_total": 0, "call_unlocked": False}

    class DummyHistory:
        def __init__(self):
            self._messages = [
                SystemMessage(content="sys"),
                HumanMessage(content="goal"),
                AIMessage(content="goal response"),
                HumanMessage(content="prior clarify"),
            ]

        async def aget_messages(self):
            return list(self._messages)

    attempt_counter = {"count": 0}

    class FlakyLLM:
        async def ainvoke(self, _messages):
            attempt_counter["count"] += 1
            if attempt_counter["count"] < 3:
                raise TimeoutError("temporary outage")
            return SimpleNamespace(content='{"reply": "Recovered"}')

    async def fake_get_history(_session_id):
        return DummyHistory()

    monkeypatch.setattr("src.services.chat_service.session_manager", DummySessionManager())
    monkeypatch.setattr("src.services.chat_service.get_history", fake_get_history)
    monkeypatch.setattr("src.services.chat_service.llm", FlakyLLM())

    result = await chat_service.ask(
        session_id="session-1",
        message="hello",
        page="micro-landing",
        section="hero",
    )

    assert result.response.reply == "Recovered"
    assert attempt_counter["count"] == 3
    assert LLM_CIRCUIT_BREAKER.cooldown_remaining("llm:chat") == 0


@pytest.mark.asyncio
async def test_chat_service_circuit_breaker_short_circuits(monkeypatch, no_retry_delay):
    """Circuit breaker should trip after repeated failures and short-circuit subsequent calls."""

    class DummySessionManager:
        async def get_session_progress(self, _session_id):
            return {"missions": [], "points_total": 0, "call_unlocked": False}

    class DummyHistory:
        def __init__(self):
            self._messages = [
                SystemMessage(content="sys"),
                HumanMessage(content="goal"),
                AIMessage(content="goal response"),
                HumanMessage(content="prior clarify"),
            ]

        async def aget_messages(self):
            return list(self._messages)

    class BrokenLLM:
        def __init__(self):
            self.calls = 0

        async def ainvoke(self, _messages):
            self.calls += 1
            raise TimeoutError("permanent failure")

    llm_stub = BrokenLLM()

    async def fake_get_history(_session_id):
        return DummyHistory()

    monkeypatch.setattr("src.services.chat_service.session_manager", DummySessionManager())
    monkeypatch.setattr("src.services.chat_service.get_history", fake_get_history)
    monkeypatch.setattr("src.services.chat_service.llm", llm_stub)

    with pytest.raises(HTTPException) as exc_info:
        await chat_service.ask(
            session_id="session-2",
            message="hello",
            page="micro-landing",
            section="hero",
        )

    assert exc_info.value.status_code == 503
    assert llm_stub.calls == 3

    with pytest.raises(HTTPException) as exc_info2:
        await chat_service.ask(
            session_id="session-2",
            message="hello again",
            page="micro-landing",
            section="hero",
        )

    assert exc_info2.value.status_code == 503
    assert llm_stub.calls == 3  # Short-circuited; no new invocations
    assert LLM_CIRCUIT_BREAKER.cooldown_remaining("llm:chat") > 0


@pytest.mark.asyncio
async def test_chat_route_rolls_back_on_history_failure(
    monkeypatch,
    async_client,
    authenticated_headers,
):
    """Chat route should rollback persisted messages when storage fails."""

    async def fake_ask(**kwargs):
        response = ChatResponse(
            reply="ok",
            history=[HumanMessage(content=kwargs["message"]), AIMessage(content="ok")],
            followUpMissions=None,
            updatedProgress=None,
            suggestedRead=None,
            navigate=None,
        )
        messages = [HumanMessage(content="hi"), AIMessage(content='{"reply": "ok"}')]
        return ChatServiceResult(response=response, messages_to_persist=messages)

    async def failing_append(_session_id, _messages):
        raise RuntimeError("db offline")

    rollback_calls = {}

    async def fake_rollback(session_id, count):
        rollback_calls["session_id"] = session_id
        rollback_calls["count"] = count

    monkeypatch.setattr("src.routes.chat.chat_service.ask", fake_ask)
    monkeypatch.setattr("src.routes.chat.append_history_messages", failing_append)
    monkeypatch.setattr("src.routes.chat.rollback_last_messages", fake_rollback)

    chat_payload = {
        "message": "Test",
        "context": {"page": "micro-landing", "section": "hero"},
    }

    response = await async_client.post(
        "/api/chat",
        json=chat_payload,
        headers=authenticated_headers,
    )

    body = response.json()

    assert response.status_code == 500
    assert body["detail"]["error_code"] == "DATABASE_FAILURE"
    assert rollback_calls["count"] == 2
    assert "session_id" in rollback_calls


@pytest.mark.asyncio
async def test_parse_goal_circuit_breaker_translates_to_http(monkeypatch):
    """Goal parser should surface circuit breaker as HTTP 503 for the route layer."""

    class DummyHistory:
        async def aget_messages(self):
            return []

    async def fake_get_history(_session_id):
        return DummyHistory()

    async def raise_circuit_breaker(*_args, **_kwargs):
        raise CircuitBreakerOpenError("llm:goal", retry_after=12.0)

    monkeypatch.setattr("src.services.goal_parser.get_history", fake_get_history)
    monkeypatch.setattr("src.services.goal_parser.async_retry", raise_circuit_breaker)

    with pytest.raises(HTTPException) as exc_info:
        await parse_user_goal("Build an AI agent", "session-3")

    assert exc_info.value.status_code == 503
