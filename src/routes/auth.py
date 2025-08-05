"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ..models.auth import (
    SessionResponse, 
    RefreshRequest, 
    RefreshResponse,
    RevokeRequest, 
    RevokeResponse
)
from ..auth.jwt_utils import jwt_manager
from ..auth.middleware import get_current_session
from ..services.session_manager import session_manager
from ..utils.errors import raise_http_error, create_error_response

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/session", response_model=SessionResponse)
async def create_session():
    """
    Create a new anonymous session with JWT tokens.
    
    **Description:**
    This is the entry point for all users. Creates a new session and returns 
    JWT access and refresh tokens that expire in 1 year. No authentication 
    required - this creates the initial session.
    
    **When to use:**
    - At the start of a user's journey (app initialization)
    - When no valid session exists
    - For anonymous users who want to start using the platform
    
    **Request:**
    No request body required - this is a simple POST request.
    
    **Response Example:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "expires_in": 31536000,
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_expires_in": 31536000
    }
    ```
    
    **Usage Example:**
    ```javascript
    const response = await fetch('/api/auth/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    const { access_token, refresh_token } = await response.json();
    
    // Store tokens for future requests
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    ```
    
    **Error Cases:**
    - **500 Internal Server Error**: JWT generation failed (server issue)
    
    **Notes:**
    - Tokens expire in 1 year (31,536,000 seconds)
    - Store both tokens securely on the client
    - Use access_token for authenticated requests
    - Use refresh_token to get new tokens when needed
    """
    try:
        # Generate session ID and tokens
        session_id = jwt_manager.generate_session_id()
        access_token = jwt_manager.create_access_token(session_id)
        refresh_token = jwt_manager.create_refresh_token(session_id)
        
        # Create session in memory
        await session_manager.create_session(session_id)
        
        return SessionResponse(
            access_token=access_token,
            expires_in=jwt_manager.expiry_seconds,
            refresh_token=refresh_token,
            refresh_expires_in=jwt_manager.expiry_seconds
        )
    except Exception as e:
        raise_http_error(500, "JWT generation failed")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest):
    """
    Exchange a valid refresh token for new access and refresh tokens.
    
    **Description:**
    Rotates JWT tokens using a valid refresh token. This endpoint provides 
    a security mechanism to get fresh tokens without requiring the user to 
    re-authenticate. The old refresh token is automatically revoked.
    
    **When to use:**
    - Before making API calls with an expired or soon-to-expire access token
    - Periodically to maintain session security (token rotation)
    - When you want to ensure you have the latest tokens
    - In response to 401 errors from other endpoints
    
    **Request Body:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    **Response Example:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "expires_in": 31536000,
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_expires_in": 31536000
    }
    ```
    
    **Usage Example:**
    ```javascript
    const refreshToken = localStorage.getItem('refresh_token');
    
    const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (response.ok) {
        const { access_token, refresh_token } = await response.json();
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
    }
    ```
    
    **Error Cases:**
    - **400 Bad Request**: Missing or malformed refresh_token in request body
    - **401 Unauthorized**: Invalid, expired, or revoked refresh token
    - **401 Unauthorized**: Session no longer exists
    - **500 Internal Server Error**: JWT rotation failed (server issue)
    
    **Security Notes:**
    - Old refresh token is automatically revoked after successful rotation
    - Always update stored tokens with the new ones returned
    - Refresh tokens have the same expiry as access tokens (1 year)
    - Failed refresh attempts may indicate compromised tokens
    """
    try:
        # Validate refresh token
        if await session_manager.is_token_revoked(request.refresh_token):
            raise_http_error(401, "Refresh token has been revoked")
        
        # Decode the refresh token to get session ID
        session_id = jwt_manager.get_session_id_from_token(request.refresh_token)
        
        # Check if session exists
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            raise_http_error(401, "Session not found")
        
        # Generate new tokens
        new_access_token = jwt_manager.create_access_token(session_id)
        new_refresh_token = jwt_manager.create_refresh_token(session_id)
        
        # Optionally revoke old refresh token
        await session_manager.revoke_token(request.refresh_token)
        
        return RefreshResponse(
            access_token=new_access_token,
            expires_in=jwt_manager.expiry_seconds,
            refresh_token=new_refresh_token,
            refresh_expires_in=jwt_manager.expiry_seconds
        )
    except HTTPException:
        raise
    except Exception as e:
        raise_http_error(500, "JWT rotation failed")


@router.delete("/session", response_model=RevokeResponse)
async def revoke_session(
    request: RevokeRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Revoke (blacklist) a refresh token, ending the session.
    
    **Description:**
    Explicitly revokes a refresh token, making it unusable for future token 
    refreshes. This is a security endpoint for "logout" functionality or when 
    you suspect a token has been compromised.
    
    **When to use:**
    - User logout functionality
    - When you suspect a token has been compromised
    - To clean up old sessions
    - Security best practice when user changes sensitive account details
    
    **Authentication Required:**
    This endpoint requires a valid Bearer token in the Authorization header.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    Content-Type: application/json
    ```
    
    **Request Body:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    **Response Example:**
    ```json
    {
        "revoked": true
    }
    ```
    
    **Usage Example:**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    const response = await fetch('/api/auth/session', {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (response.ok) {
        // Clean up stored tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Redirect to login page
        window.location.href = '/login';
    }
    ```
    
    **Error Cases:**
    - **400 Bad Request**: Missing refresh_token in request body
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **401 Unauthorized**: Invalid or expired access token
    - **500 Internal Server Error**: Revocation failed (server issue)
    
    **Security Notes:**
    - Once revoked, the refresh token cannot be used again
    - The access token remains valid until its natural expiration
    - Consider this a "soft logout" - user can still use access token temporarily
    - For complete logout, client should also discard the access token
    """
    try:
        # Add token to revoked list
        await session_manager.revoke_token(request.refresh_token)
        
        return RevokeResponse(revoked=True)
    except Exception as e:
        raise_http_error(500, "Revocation failed")