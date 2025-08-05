"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.services.session_manager import SessionManager


@pytest.fixture
def client():
    """Synchronous test client for FastAPI."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """Asynchronous test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def session_manager():
    """Fresh session manager for each test."""
    return SessionManager()


@pytest_asyncio.fixture
async def sample_session(session_manager):
    """Create a sample session for testing."""
    session_id = "test-session-123"
    session_data = await session_manager.create_session(session_id)
    return session_data


@pytest_asyncio.fixture
async def authenticated_headers(async_client):
    """Get authentication headers with valid token."""
    # Create a session first
    response = await async_client.post("/api/auth/session")
    assert response.status_code == 200
    
    session_data = response.json()
    access_token = session_data["access_token"]
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


@pytest_asyncio.fixture
async def goal_submitted_session(async_client, authenticated_headers):
    """Session with a goal already submitted."""
    goal_data = {"input": "I want to build an AI agent for restaurants"}
    response = await async_client.post(
        "/api/goal", 
        json=goal_data, 
        headers=authenticated_headers
    )
    assert response.status_code == 200
    return response.json(), authenticated_headers