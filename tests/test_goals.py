"""Tests for goal and personalization endpoints."""

import pytest


class TestGoalEndpoints:
    """Test goal and personalization endpoints."""

    @pytest.mark.asyncio
    async def test_submit_goal_success(self, async_client, authenticated_headers):
        """Test successful goal submission."""
        goal_data = {"input": "I want to build an AI agent for restaurants"}
        response = await async_client.post(
            "/api/goal", 
            json=goal_data, 
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "session_id" in data
        assert "goal" in data
        assert "missions" in data
        assert "headline" in data
        assert "recommended_case_studies" in data
        
        # Check goal structure
        goal = data["goal"]
        assert "description" in goal
        assert "category" in goal
        assert "priority" in goal
        
        # Check missions
        missions = data["missions"]
        assert len(missions) > 0
        for mission in missions:
            assert "id" in mission
            assert "title" in mission
            assert "points" in mission
            assert "status" in mission
        
        # Check case studies
        case_studies = data["recommended_case_studies"]
        assert len(case_studies) > 0
        for case_study in case_studies:
            assert "id" in case_study
            assert "title" in case_study
            assert "summary" in case_study

    @pytest.mark.asyncio
    async def test_submit_goal_empty_input(self, async_client, authenticated_headers):
        """Test goal submission with empty input."""
        goal_data = {"input": ""}
        response = await async_client.post(
            "/api/goal", 
            json=goal_data, 
            headers=authenticated_headers
        )
        
        assert response.status_code == 400
        assert "error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_submit_goal_unauthorized(self, async_client):
        """Test goal submission without authorization."""
        goal_data = {"input": "I want to build something"}
        response = await async_client.post("/api/goal", json=goal_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_clarify_goal_success(self, async_client, goal_submitted_session):
        """Test successful goal clarification."""
        goal_response, headers = goal_submitted_session
        
        clarify_data = {"clarification": "Focus on customer satisfaction"}
        response = await async_client.post(
            "/api/clarify", 
            json=clarify_data, 
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "goal" in data
        assert "missions" in data
        assert "headline" in data
        assert "recommended_case_studies" in data
        
        # Goal should be updated
        assert "customer satisfaction" in data["goal"]["description"].lower()

    @pytest.mark.asyncio
    async def test_clarify_goal_empty(self, async_client, goal_submitted_session):
        """Test goal clarification with empty input."""
        _, headers = goal_submitted_session
        
        clarify_data = {"clarification": ""}
        response = await async_client.post(
            "/api/clarify", 
            json=clarify_data, 
            headers=headers
        )
        
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_clarify_goal_no_goal(self, async_client, authenticated_headers):
        """Test clarifying goal when no goal exists."""
        clarify_data = {"clarification": "Some clarification"}
        response = await async_client.post(
            "/api/clarify", 
            json=clarify_data, 
            headers=authenticated_headers
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_personalized_content(self, async_client, goal_submitted_session):
        """Test getting personalized content."""
        _, headers = goal_submitted_session
        
        response = await async_client.get("/api/personalised", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "headline" in data
        assert "goal" in data
        assert "missions" in data
        assert "recommended_case_studies" in data

    @pytest.mark.asyncio
    async def test_get_personalized_content_no_goal(self, async_client, authenticated_headers):
        """Test getting personalized content when no goal exists."""
        response = await async_client.get("/api/personalised", headers=authenticated_headers)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_personalized_content_unauthorized(self, async_client):
        """Test getting personalized content without authorization."""
        response = await async_client.get("/api/personalised")
        
        assert response.status_code == 401