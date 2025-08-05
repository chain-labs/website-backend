"""Tests for authentication endpoints."""

import pytest
import jwt
from datetime import datetime, timezone

from src.auth.jwt_utils import jwt_manager


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_create_session(self, async_client):
        """Test creating a new session."""
        response = await async_client.post("/api/auth/session")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "expires_in" in data
        assert "refresh_token" in data
        assert "refresh_expires_in" in data
        
        # Check expiry times
        assert data["expires_in"] == 31536000  # 1 year
        assert data["refresh_expires_in"] == 31536000
        
        # Verify tokens are valid JWTs
        access_payload = jwt.decode(
            data["access_token"], 
            jwt_manager.secret_key, 
            algorithms=[jwt_manager.algorithm]
        )
        assert "session_id" in access_payload
        assert "exp" in access_payload
        assert "iat" in access_payload

    @pytest.mark.asyncio
    async def test_refresh_token_valid(self, async_client):
        """Test refreshing with valid token."""
        # Create session first
        session_response = await async_client.post("/api/auth/session")
        assert session_response.status_code == 200
        session_data = session_response.json()
        
        # Refresh token
        refresh_data = {"refresh_token": session_data["refresh_token"]}
        response = await async_client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check new tokens are provided
        assert "access_token" in data
        assert "refresh_token" in data
        # Note: tokens might be the same if generated at same timestamp

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, async_client):
        """Test refreshing with invalid token."""
        refresh_data = {"refresh_token": "invalid-token"}
        response = await async_client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_missing(self, async_client):
        """Test refresh with missing token."""
        response = await async_client.post("/api/auth/refresh", json={})
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_revoke_session(self, async_client, authenticated_headers):
        """Test revoking a session."""
        # Create session first
        session_response = await async_client.post("/api/auth/session")
        session_data = session_response.json()
        
        revoke_data = {"refresh_token": session_data["refresh_token"]}
        response = await async_client.request(
            "DELETE",
            "/api/auth/session", 
            json=revoke_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["revoked"] is True

    @pytest.mark.asyncio
    async def test_revoke_session_unauthorized(self, async_client):
        """Test revoking session without auth."""
        revoke_data = {"refresh_token": "some-token"}
        response = await async_client.request("DELETE", "/api/auth/session", json=revoke_data)
        
        assert response.status_code == 401