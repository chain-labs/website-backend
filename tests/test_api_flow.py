"""Integration tests for goal -> clarify -> chat flow."""

import json
from typing import List, Tuple

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.services.goal_parser import ParsedLLMResult
from src.services.chat_service import ChatServiceResult
from src.models.chat import ChatResponse


@pytest.mark.asyncio
async def test_full_goal_clarify_chat_flow(async_client, monkeypatch):
    """Verify the end-to-end flow succeeds with consistent history handling."""

    # Create a session and capture auth headers
    session_response = await async_client.post("/api/auth/session")
    assert session_response.status_code == 200
    token = session_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Patch history persistence to avoid hitting the real store while recording calls
    appended_records: List[Tuple[str, List[BaseMessage]]] = []
    rollback_records: List[Tuple[str, int]] = []

    async def fake_append_history(session_id, messages):
        appended_records.append((session_id, list(messages)))

    async def fake_rollback(session_id, count):
        rollback_records.append((session_id, count))

    monkeypatch.setattr("src.routes.goals.append_history_messages", fake_append_history)
    monkeypatch.setattr("src.routes.goals.rollback_last_messages", fake_rollback)
    monkeypatch.setattr("src.routes.chat.append_history_messages", fake_append_history)
    monkeypatch.setattr("src.routes.chat.rollback_last_messages", fake_rollback)

    # Stub goal parsing to return deterministic content and recorded messages
    async def fake_parse_goal(user_prompt, session_id):
        return ParsedLLMResult(
            content="Thanks for sharing your goal!",
            messages_to_persist=[
                SystemMessage(content="goal-system"),
                HumanMessage(content=user_prompt),
                AIMessage(content="{\"reply\": \"Thanks for sharing your goal!\"}"),
            ],
            raw_response={
                "isValidGoal": True,
                "clarificationQuestion": "Thanks for sharing your goal!",
                "errorMessage": None,
            },
        )

    monkeypatch.setattr("src.routes.goals.parse_user_goal", fake_parse_goal)

    # Stub clarification parsing to return structured payload and history messages
    clarify_payload = {
        "hero": {"title": "Hero", "description": "Desc"},
        "process": [{"name": "Plan", "description": "Do things"}],
        "goal": "Clarified goal",
        "caseStudies": [
            {
                "id": "case1",
                "title": "Case Study",
                "description": "Details",
                "shortDescription": "Short",
                "thumbnail": "thumb",
                "fallbackImage": "img",
            }
        ],
        "whyThisCaseStudiesWereSelected": "Because",
        "missions": [
            {
                "id": "mission-one",
                "title": "Mission",
                "description": "Mission details",
                "points": 15,
                "status": "pending",
                "icon": "icon",
                "input": {"required": False, "type": "text", "placeholder": ""},
                "missionType": "default",
                "options": {"targetCaseStudyId": "case1"},
            }
        ],
        "why": "Why not",
        "fallbackToGenericData": False,
    }

    clarify_wrapper = {
        "isValidClarification": True,
        "personalizedPitch": clarify_payload,
        "errorMessage": None,
    }

    async def fake_parse_clarification(user_prompt, session_id):
        return ParsedLLMResult(
            content=clarify_wrapper,
            messages_to_persist=[
                HumanMessage(content=user_prompt),
                AIMessage(content=json.dumps(clarify_payload)),
            ],
            raw_response=clarify_wrapper,
        )

    monkeypatch.setattr("src.routes.goals.parse_user_clarification", fake_parse_clarification)

    # Stub chat response generation with deterministic reply & history to persist
    async def fake_chat_ask(session_id, message, page, section):
        reply = f"Assistant response to: {message}"
        response = ChatResponse(
            reply=reply,
            history=[],
            followUpMissions=None,
            updatedProgress=None,
            suggestedRead=None,
            navigate=None,
        )
        persisted_history = [
            HumanMessage(content=message),
            AIMessage(content=f"```json\n{{\"reply\": \"{reply}\"}}\n```"),
        ]
        return ChatServiceResult(response=response, messages_to_persist=persisted_history)

    monkeypatch.setattr("src.routes.chat.chat_service.ask", fake_chat_ask)

    # Submit a goal
    goal_response = await async_client.post(
        "/api/goal",
        json={"input": "I want to build an agent"},
        headers=headers,
    )
    assert goal_response.status_code == 200
    assert goal_response.json()["assistantMessage"]["message"] == "Thanks for sharing your goal!"

    # Clarify the goal
    clarify_response = await async_client.post(
        "/api/clarify",
        json={"clarification": "Make it focus on onboarding"},
        headers=headers,
    )
    assert clarify_response.status_code == 200
    assert clarify_response.json()["goal"] == "Clarified goal"

    # Chat with assistant
    chat_response = await async_client.post(
        "/api/chat",
        json={
            "message": "What should I do next?",
            "context": {"page": "mission-dashboard", "section": "overview"},
        },
        headers=headers,
    )
    assert chat_response.status_code == 200
    assert "Assistant response" in chat_response.json()["reply"]

    # Ensure history persistence was attempted exactly three times (goal, clarify, chat)
    assert len(appended_records) == 3
    session_ids = {session for session, _ in appended_records}
    assert len(session_ids) == 1
    assert not rollback_records


@pytest.mark.asyncio
async def test_chat_history_rolls_back_on_persist_failure(async_client, monkeypatch):
    """Ensure chat history rollback triggers when persistence fails."""

    session_response = await async_client.post("/api/auth/session")
    assert session_response.status_code == 200
    token = session_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def fake_chat_ask(session_id, message, page, section):
        reply = "Assistant reply"
        response = ChatResponse(
            reply=reply,
            history=[],
            followUpMissions=None,
            updatedProgress=None,
            suggestedRead=None,
            navigate=None,
        )
        persisted_history = [
            HumanMessage(content=message),
            AIMessage(content="```json\n{\"reply\": \"Assistant reply\"}\n```"),
        ]
        return ChatServiceResult(response=response, messages_to_persist=persisted_history)

    monkeypatch.setattr("src.routes.chat.chat_service.ask", fake_chat_ask)

    async def failing_append(session_id, messages):  # pylint: disable=unused-argument
        raise RuntimeError("storage down")

    rollback_calls: List[Tuple[str, int]] = []

    async def record_rollback(session_id, count):
        rollback_calls.append((session_id, count))

    monkeypatch.setattr("src.routes.chat.append_history_messages", failing_append)
    monkeypatch.setattr("src.routes.chat.rollback_last_messages", record_rollback)

    response = await async_client.post(
        "/api/chat",
        json={
            "message": "Testing failure",
            "context": {"page": "mission-dashboard", "section": "overview"},
        },
        headers=headers,
    )

    assert response.status_code == 500
    detail = response.json()["detail"]["error"]["message"]
    assert detail == "Failed to persist chat history"
    assert rollback_calls
    assert rollback_calls[0][1] == 2
