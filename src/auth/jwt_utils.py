"""JWT utilities for token generation and validation."""

import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import secrets
import uuid

from ..models.auth import TokenPayload
from ..utils.errors import raise_http_error
from scripts.generate_secret import generate_jwt_secret


# Secret key for JWT signing from environment variable
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", generate_jwt_secret())
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 31536000  # 1 year as specified


class JWTManager:
    """JWT token management."""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.expiry_seconds = TOKEN_EXPIRY_SECONDS
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    def create_access_token(self, session_id: str) -> str:
        """Create an access token with session ID."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=self.expiry_seconds)
        
        payload = {
            "session_id": session_id,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, session_id: str) -> str:
        """Create a refresh token (same as access token for simplicity)."""
        return self.create_access_token(session_id)
    
    def decode_token(self, token: str) -> TokenPayload:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            # Ensure required fields exist
            if 'session_id' not in payload:
                raise jwt.InvalidTokenError("Missing session_id in token")
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise_http_error(401, "Token has expired")
        except jwt.InvalidTokenError:
            raise_http_error(401, "Invalid token")
    
    def get_session_id_from_token(self, token: str) -> str:
        """Extract session ID from token."""
        payload = self.decode_token(token)
        return payload.session_id


# Global JWT manager instance
jwt_manager = JWTManager()