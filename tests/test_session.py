"""Tests for session management endpoints."""

import pytest


class TestSessionEndpoints:
    """Test session management endpoints."""

    @pytest.mark.asyncio
    async def test_get_full_session_with_goal(self, async_client, goal_submitted_session):
        """Test getting full session data after goal submission."""
        _, headers = goal_submitted_session
        
        response = await async_client.get("/api/session", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "goal" in data
        assert "missions" in data
        assert "points_total" in data
        assert "call_unlocked" in data
        
        # Check goal exists
        goal = data["goal"]
        assert "description" in goal
        assert "category" in goal
        
        # Check missions
        missions = data["missions"]
        assert len(missions) > 0
        for mission in missions:
            assert "id" in mission
            assert "status" in mission
            assert "points" in mission
        
        # Initial state
        assert data["points_total"] == 0
        assert data["call_unlocked"] is False

    @pytest.mark.asyncio
    async def test_get_full_session_no_goal(self, async_client, authenticated_headers):
        """Test getting session data when no goal exists."""
        response = await async_client.get("/api/session", headers=authenticated_headers)
        
        assert response.status_code == 404
        assert "error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_full_session_unauthorized(self, async_client):
        """Test getting session data without authorization."""
        response = await async_client.get("/api/session")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_after_mission_completion(self, async_client, goal_submitted_session):
        """Test session data reflects mission completion."""
        goal_response, headers = goal_submitted_session
        
        # Complete a mission first
        missions = goal_response["missions"]
        first_mission = missions[0]
        
        completion_data = {
            "mission_id": first_mission["id"],
            "artifact": {"answer": "My solution"}
        }
        
        completion_response = await async_client.post(
            "/api/mission/complete", 
            json=completion_data, 
            headers=headers
        )
        assert completion_response.status_code == 200
        
        # Now get session data
        session_response = await async_client.get("/api/session", headers=headers)
        assert session_response.status_code == 200
        
        data = session_response.json()
        
        # Points should be updated
        assert data["points_total"] == first_mission["points"]
        
        # Mission status should be updated
        completed_mission = next(
            (m for m in data["missions"] if m["id"] == first_mission["id"]), 
            None
        )
        assert completed_mission is not None
        assert completed_mission["status"] == "completed"


class TestIntegrationFlow:
    """Test complete integration flows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_user_flow(self, async_client):
        """Test complete user flow from session creation to mission completion."""
        # 1. Create session
        session_response = await async_client.post("/api/auth/session")
        assert session_response.status_code == 200
        session_data = session_response.json()
        
        headers = {
            "Authorization": f"Bearer {session_data['access_token']}",
            "Content-Type": "application/json"
        }
        
        # 2. Submit goal
        goal_data = {"input": "I want to build an AI agent for restaurants"}
        goal_response = await async_client.post(
            "/api/goal", 
            json=goal_data, 
            headers=headers
        )
        assert goal_response.status_code == 200
        goal_result = goal_response.json()
        
        # 3. Check initial progress
        progress_response = await async_client.get("/api/progress", headers=headers)
        assert progress_response.status_code == 200
        initial_progress = progress_response.json()
        assert initial_progress["points_total"] == 0
        assert initial_progress["call_unlocked"] is False
        
        # 4. Complete first mission
        missions = goal_result["missions"]
        first_mission = missions[0]
        
        completion_data = {
            "mission_id": first_mission["id"],
            "artifact": {"answer": "Completed first mission"}
        }
        
        complete_response = await async_client.post(
            "/api/mission/complete", 
            json=completion_data, 
            headers=headers
        )
        assert complete_response.status_code == 200
        completion_result = complete_response.json()
        assert completion_result["points_awarded"] == first_mission["points"]
        assert completion_result["call_unlocked"] is False
        
        # 5. Complete second mission to unlock call
        second_mission = missions[1]
        completion_data2 = {
            "mission_id": second_mission["id"],
            "artifact": {"answer": "Completed second mission"}
        }
        
        complete_response2 = await async_client.post(
            "/api/mission/complete", 
            json=completion_data2, 
            headers=headers
        )
        assert complete_response2.status_code == 200
        completion_result2 = complete_response2.json()
        assert completion_result2["call_unlocked"] is True
        
        # 6. Check unlock status
        unlock_response = await async_client.get("/api/unlock-status", headers=headers)
        assert unlock_response.status_code == 200
        assert unlock_response.json()["call_unlocked"] is True
        
        # 7. Get final session state
        final_session_response = await async_client.get("/api/session", headers=headers)
        assert final_session_response.status_code == 200
        final_session = final_session_response.json()
        
        expected_points = first_mission["points"] + second_mission["points"]
        assert final_session["points_total"] == expected_points
        assert final_session["call_unlocked"] is True
        
        # Check completed missions
        completed_count = sum(
            1 for m in final_session["missions"] 
            if m["status"] == "completed"
        )
        assert completed_count == 2