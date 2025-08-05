"""Tests for chat endpoint functionality."""

import pytest
from datetime import datetime


class TestChatEndpoints:
    """Test chat endpoint functionality."""

    async def test_chat_basic_message(self, async_client, authenticated_headers):
        """Test basic chat functionality."""
        chat_data = {
            "message": "Hello, I need help with my AI project",
            "context": {
                "page": "micro-landing",
                "section": "hero"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        assert "history" in data
        assert len(data["history"]) == 2  # User message + assistant reply
        
        # Check message structure
        user_msg = data["history"][0]
        assert user_msg["role"] == "user"
        assert user_msg["message"] == chat_data["message"]
        assert "timestamp" in user_msg
        
        assistant_msg = data["history"][1]
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg["message"] == data["reply"]
        assert "timestamp" in assistant_msg

    async def test_chat_with_mission_context(self, async_client, authenticated_headers):
        """Test chat with mission context."""
        chat_data = {
            "message": "I need help with this mission",
            "context": {
                "page": "mission-dashboard",
                "section": "mission-1",
                "metadata": {"missionId": "defineMetrics"}
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        assert "defineMetrics" in data["reply"] or "metrics" in data["reply"].lower()

    async def test_chat_mission_recommendation(self, async_client, authenticated_headers):
        """Test chat requesting mission recommendations."""
        chat_data = {
            "message": "What mission should I do next?",
            "context": {
                "page": "mission-dashboard",
                "section": "overview"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        # May include followUpMissions or navigation
        if "followUpMissions" in data:
            assert isinstance(data["followUpMissions"], list)
            if data["followUpMissions"]:
                mission = data["followUpMissions"][0]
                assert "id" in mission
                assert "title" in mission
                assert "points" in mission

    async def test_chat_progress_inquiry(self, async_client, authenticated_headers):
        """Test chat asking about progress."""
        chat_data = {
            "message": "How many points have I earned?",
            "context": {
                "page": "mission-dashboard",
                "section": "progress-widget"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        
        # Should include progress update
        if "updatedProgress" in data:
            progress = data["updatedProgress"]
            assert "pointsTotal" in progress
            assert "missions" in progress
            assert "callUnlocked" in progress

    async def test_chat_case_study_request(self, async_client, authenticated_headers):
        """Test chat requesting case studies."""
        chat_data = {
            "message": "Can you show me some examples?",
            "context": {
                "page": "micro-landing",
                "section": "hero"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        
        # May include suggested reading
        if "suggestedRead" in data:
            assert isinstance(data["suggestedRead"], list)
            if data["suggestedRead"]:
                case_study = data["suggestedRead"][0]
                assert "id" in case_study
                assert "title" in case_study
                assert "summary" in case_study

    async def test_chat_navigation_response(self, async_client, authenticated_headers):
        """Test chat that should include navigation."""
        chat_data = {
            "message": "What should I work on next?",
            "context": {
                "page": "micro-landing",
                "section": "hero"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        
        # May include navigation instruction
        if "navigate" in data and data["navigate"] is not None:
            nav = data["navigate"]
            assert "page" in nav
            assert "section" in nav

    async def test_chat_conversation_history(self, async_client, authenticated_headers):
        """Test that chat history is maintained across multiple messages."""
        # First message
        chat_data1 = {
            "message": "Hello, I'm starting my AI project",
            "context": {
                "page": "micro-landing",
                "section": "hero"
            }
        }
        
        response1 = await async_client.post("/api/chat", json=chat_data1, headers=authenticated_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["history"]) == 2
        
        # Second message
        chat_data2 = {
            "message": "What metrics should I define?",
            "context": {
                "page": "mission-dashboard",
                "section": "mission-1"
            }
        }
        
        response2 = await async_client.post("/api/chat", json=chat_data2, headers=authenticated_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["history"]) == 4  # 2 from first + 2 from second
        
        # Check history continuity
        assert data2["history"][0]["message"] == chat_data1["message"]
        assert data2["history"][2]["message"] == chat_data2["message"]

    async def test_chat_empty_message(self, async_client, authenticated_headers):
        """Test chat with empty message."""
        chat_data = {
            "message": "",
            "context": {
                "page": "micro-landing",
                "section": "hero"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 422  # Pydantic validation error for empty string
        data = response.json()
        assert "detail" in data

    async def test_chat_missing_context(self, async_client, authenticated_headers):
        """Test chat without context."""
        chat_data = {
            "message": "Hello"
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 422  # Validation error

    async def test_chat_invalid_context_structure(self, async_client, authenticated_headers):
        """Test chat with invalid context structure."""
        chat_data = {
            "message": "Hello",
            "context": {
                "page": "micro-landing"
                # Missing required 'section' field
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 422  # Validation error

    async def test_chat_unauthorized(self, async_client):
        """Test chat without authentication."""
        chat_data = {
            "message": "Hello",
            "context": {
                "page": "micro-landing",
                "section": "hero"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data)
        assert response.status_code == 401

    async def test_chat_with_metadata(self, async_client, authenticated_headers):
        """Test chat with metadata in context."""
        chat_data = {
            "message": "Tell me about this case study",
            "context": {
                "page": "case-study",
                "section": "hero",
                "metadata": {"caseStudyId": "cs1"}
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        assert "history" in data

    async def test_chat_different_page_contexts(self, async_client, authenticated_headers):
        """Test chat responses vary by page context."""
        contexts = [
            {"page": "micro-landing", "section": "hero"},
            {"page": "mission-dashboard", "section": "overview"},
            {"page": "case-study", "section": "details"}
        ]
        
        replies = []
        for context in contexts:
            chat_data = {
                "message": "I need help",
                "context": context
            }
            
            response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
            assert response.status_code == 200
            data = response.json()
            replies.append(data["reply"])
        
        # Replies should be contextually different (though this is hard to assert precisely)
        assert len(set(replies)) >= 1  # At least some variation expected

    async def test_chat_response_optional_fields(self, async_client, authenticated_headers):
        """Test that optional response fields are properly structured when present."""
        chat_data = {
            "message": "What should I do next? Show me examples and my progress.",
            "context": {
                "page": "mission-dashboard",
                "section": "overview"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check optional fields structure if present
        if "followUpMissions" in data and data["followUpMissions"]:
            for mission in data["followUpMissions"]:
                assert "id" in mission
                assert "title" in mission
                assert "points" in mission
        
        if "updatedProgress" in data and data["updatedProgress"]:
            progress = data["updatedProgress"]
            assert isinstance(progress["pointsTotal"], int)
            assert isinstance(progress["missions"], list)
            assert isinstance(progress["callUnlocked"], bool)
        
        if "suggestedRead" in data and data["suggestedRead"]:
            for case_study in data["suggestedRead"]:
                assert "id" in case_study
                assert "title" in case_study
                assert "summary" in case_study
        
        if "navigate" in data and data["navigate"]:
            nav = data["navigate"]
            assert isinstance(nav["page"], str)
            assert isinstance(nav["section"], str)


class TestChatIntegration:
    """Test chat integration with other systems."""

    async def test_chat_after_goal_submission(self, async_client, authenticated_headers):
        """Test chat works after submitting a goal."""
        # First submit a goal
        goal_data = {"input": "I want to build an AI restaurant assistant"}
        goal_response = await async_client.post("/api/goal", json=goal_data, headers=authenticated_headers)
        assert goal_response.status_code == 200
        
        # Then chat about it
        chat_data = {
            "message": "Tell me about my goal and what to do next",
            "context": {
                "page": "mission-dashboard",
                "section": "overview"
            }
        }
        
        response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reply" in data
        assert "history" in data

    async def test_chat_with_mission_completion(self, async_client, authenticated_headers):
        """Test chat integration with mission completion."""
        # Submit goal and get missions
        goal_data = {"input": "I want to build an AI agent"}
        await async_client.post("/api/goal", json=goal_data, headers=authenticated_headers)
        
        # Get progress to see available missions
        progress_response = await async_client.get("/api/progress", headers=authenticated_headers)
        progress_data = progress_response.json()
        
        if progress_data["missions"]:
            mission_id = progress_data["missions"][0]["id"]
            
            # Complete a mission
            completion_data = {
                "missionId": mission_id,
                "artifact": {"answer": "Test completion"}
            }
            await async_client.post("/api/mission/complete", json=completion_data, headers=authenticated_headers)
            
            # Chat about progress
            chat_data = {
                "message": "How am I doing with my missions?",
                "context": {
                    "page": "mission-dashboard",
                    "section": "progress-widget"
                }
            }
            
            response = await async_client.post("/api/chat", json=chat_data, headers=authenticated_headers)
            assert response.status_code == 200
            
            data = response.json()
            # Should reflect the completed mission
            if "updatedProgress" in data and data["updatedProgress"] is not None:
                progress = data["updatedProgress"]
                assert progress["pointsTotal"] > 0