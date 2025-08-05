"""Authentication middleware for FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .jwt_utils import jwt_manager
from ..utils.errors import raise_http_error


# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


def get_current_session(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Dependency to get current session ID from JWT token.
    Used for protected endpoints.
    """
    if not credentials:
        raise_http_error(401, "Authorization header missing")
    
    try:
        token = credentials.credentials
        session_id = jwt_manager.get_session_id_from_token(token)
        return session_id
    except Exception as e:
        raise_http_error(401, "Invalid or expired token")


def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """
    Optional authentication dependency.
    Returns session_id if valid token provided, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        session_id = jwt_manager.get_session_id_from_token(token)
        return session_id
    except Exception:
        return None