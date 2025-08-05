"""Tests for mission and progress endpoints."""

import pytest


class TestMissionEndpoints:
    """Test mission and progress endpoints."""

    @pytest.mark.asyncio
    async def test_get_progress_initial(self, async_client, goal_submitted_session):
        """Test getting initial progress."""
        _, headers = goal_submitted_session
        
        response = await async_client.get("/api/progress", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "points_total" in data
        assert "missions" in data
        assert "call_unlocked" in data
        
        # Initial state
        assert data["points_total"] == 0
        assert data["call_unlocked"] is False
        
        # Check missions structure
        missions = data["missions"]
        assert len(missions) > 0
        for mission in missions:
            assert "id" in mission
            assert "status" in mission
            assert "points" in mission
            assert mission["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_progress_unauthorized(self, async_client):
        """Test getting progress without authorization."""
        response = await async_client.get("/api/progress")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_complete_mission_success(self, async_client, goal_submitted_session):
        """Test successful mission completion."""
        goal_response, headers = goal_submitted_session
        
        # Get first mission ID
        missions = goal_response["missions"]
        first_mission = missions[0]
        
        completion_data = {
            "mission_id": first_mission["id"],
            "artifact": {"answer": "This is my solution"}
        }
        
        response = await async_client.post(
            "/api/mission/complete", 
            json=completion_data, 
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "points_awarded" in data
        assert "points_total" in data
        assert "call_unlocked" in data
        assert "next_mission" in data
        
        # Check points
        assert data["points_awarded"] == first_mission["points"]
        assert data["points_total"] == first_mission["points"]
        
        # Should not be unlocked yet (need 2+ missions)
        assert data["call_unlocked"] is False

    @pytest.mark.asyncio
    async def test_complete_mission_twice(self, async_client, goal_submitted_session):
        """Test completing the same mission twice."""
        goal_response, headers = goal_submitted_session
        
        # Get first mission ID
        missions = goal_response["missions"]
        first_mission = missions[0]
        
        completion_data = {
            "mission_id": first_mission["id"],
            "artifact": {"answer": "This is my solution"}
        }
        
        # Complete mission first time
        response1 = await async_client.post(
            "/api/mission/complete", 
            json=completion_data, 
            headers=headers
        )
        assert response1.status_code == 200
        
        # Try to complete again
        response2 = await async_client.post(
            "/api/mission/complete", 
            json=completion_data, 
            headers=headers
        )
        assert response2.status_code == 403

    @pytest.mark.asyncio
    async def test_complete_mission_invalid_id(self, async_client, goal_submitted_session):
        """Test completing mission with invalid ID."""
        _, headers = goal_submitted_session
        
        completion_data = {
            "mission_id": "invalid-mission-id",
            "artifact": {"answer": "This is my solution"}
        }
        
        response = await async_client.post(
            "/api/mission/complete", 
            json=completion_data, 
            headers=headers
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_complete_mission_missing_artifact(self, async_client, goal_submitted_session):
        """Test completing mission without artifact."""
        goal_response, headers = goal_submitted_session
        
        missions = goal_response["missions"]
        first_mission = missions[0]
        
        completion_data = {"mission_id": first_mission["id"]}
        
        response = await async_client.post(
            "/api/mission/complete", 
            json=completion_data, 
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_complete_two_missions_unlock(self, async_client, goal_submitted_session):
        """Test that completing 2 missions unlocks the call."""
        goal_response, headers = goal_submitted_session
        
        missions = goal_response["missions"]
        first_mission = missions[0]
        second_mission = missions[1]
        
        # Complete first mission
        completion_data1 = {
            "mission_id": first_mission["id"],
            "artifact": {"answer": "Solution 1"}
        }
        response1 = await async_client.post(
            "/api/mission/complete", 
            json=completion_data1, 
            headers=headers
        )
        assert response1.status_code == 200
        assert response1.json()["call_unlocked"] is False
        
        # Complete second mission
        completion_data2 = {
            "mission_id": second_mission["id"],
            "artifact": {"answer": "Solution 2"}
        }
        response2 = await async_client.post(
            "/api/mission/complete", 
            json=completion_data2, 
            headers=headers
        )
        assert response2.status_code == 200
        
        # Should be unlocked now
        data = response2.json()
        assert data["call_unlocked"] is True
        assert data["points_total"] == first_mission["points"] + second_mission["points"]

    @pytest.mark.asyncio
    async def test_check_unlock_status(self, async_client, goal_submitted_session):
        """Test checking unlock status."""
        _, headers = goal_submitted_session
        
        response = await async_client.get("/api/unlock-status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "call_unlocked" in data
        assert data["call_unlocked"] is False  # Initially false

    @pytest.mark.asyncio
    async def test_check_unlock_status_unauthorized(self, async_client):
        """Test checking unlock status without authorization."""
        response = await async_client.get("/api/unlock-status")
        
        assert response.status_code == 401