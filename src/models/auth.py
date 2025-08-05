"""Authentication-related Pydantic models."""

from typing import Optional
from pydantic import BaseModel


class SessionResponse(BaseModel):
    """Response for creating a new session."""
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int


class RefreshRequest(BaseModel):
    """Request to refresh tokens."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Response for token refresh."""
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int


class RevokeRequest(BaseModel):
    """Request to revoke a refresh token."""
    refresh_token: str


class RevokeResponse(BaseModel):
    """Response for token revocation."""
    revoked: bool


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    session_id: str
    exp: int
    iat: int