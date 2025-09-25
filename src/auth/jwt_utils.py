"""JWT utilities for token generation and validation."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import logging
import uuid
import jwt

from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.database import get_connection
from src.utils.errors import raise_http_error

from src.config import JWT_SECRET_KEY, JWT_ALGORITHM, TOKEN_EXPIRY_SECONDS
from ..models.auth import TokenPayload


logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class JWTManager:
    """JWT token management."""

    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.expiry_seconds = TOKEN_EXPIRY_SECONDS

    async def generate_session_id(self, conn, request: Request = None) -> str:
        """Generate a unique session ID and store it in the database."""
        session_id = str(uuid.uuid4())
        user_agent = request.headers.get("user-agent") if request else None
        ip_address = request.client.host if request and hasattr(request, "client") and request.client else None
        now = datetime.now(timezone.utc)

        try:
            await conn.execute(
                """
                INSERT INTO sessions (id, user_agent, ip_address, created_at, last_activity, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (session_id, user_agent, ip_address, now, now, True)
            )

            await conn.commit()
            return session_id
        except Exception as e:
            await conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create session: {str(e)}"
            )

    async def store_session_transfer(self, conn, old_session_id, new_session_id):
        """
        Store Reset Transfer from old Session to new in db
        """
        try:
            await conn.execute(
                """
                INSERT INTO session_transfers (old_session_id, new_session_id)
                VALUES (%s, %s)
                """,
                (old_session_id, new_session_id)
            )

            await conn.commit()
        
        except Exception as e:
            await conn.rollback()
            logger.exception(
                "Failed to store session transfer",
                extra={
                    "event": "auth.session.transfer.error",
                    "old_session_id": old_session_id,
                    "new_session_id": new_session_id,
                }
            )
            raise_http_error(500, "Error during storing reset data")
    
    
    async def create_access_token(self, session_id: str) -> str:
        """Create an access token with session ID."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=self.expiry_seconds)
        
        payload = {
            "session_id": session_id,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def create_refresh_token(self, session_id: str) -> str:
        """Create a refresh token (same as access token for simplicity)."""
        return await self.create_access_token(session_id)
    
    def decode_token(self, token: str) -> TokenPayload:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_signature": True}
            )
            # Ensure required fields exist
            if 'session_id' not in payload:
                raise jwt.InvalidTokenError("Missing session_id in token")
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.JWTError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_session(self, session_id: str, conn) -> Optional[dict]:
        """Retrieve a session from the database."""
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT * FROM sessions WHERE id = %s", (session_id,)
            )
            row = await cur.fetchone()
            if row:
                # Map to your expected structure or return as dict
                return dict(row)
            return None
    
    async def update_session_activity(self, session_id: str, conn) -> None:
        """Update the last activity timestamp of a session."""
        now = datetime.now(timezone.utc)
        try:
            await conn.execute(
                "UPDATE sessions SET last_activity = %s WHERE id = %s",
                (now, session_id)
            )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.exception(
                "Failed to update session activity",
                extra={
                    "event": "auth.session.activity.error",
                    "session_id": session_id,
                }
            )
            raise

    
    def get_session_id_from_token(self, token: str) -> str:
        """Extract session ID from token."""
        payload = self.decode_token(token)
        return payload.session_id


# Global JWT manager instance
jwt_manager = JWTManager()

async def get_current_session(
    request: Request,
    conn = Depends(get_connection),
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Dependency to get current session from JWT token."""

    try:
        payload = jwt_manager.decode_token(token)
        session = await jwt_manager.get_session(payload.session_id, conn)
        if not session or not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive session",
                headers={"WWW-Authenticate": "Bearer"},
            )
        await jwt_manager.update_session_activity(payload.session_id, conn)
        request.state.session = session
        return session
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise 
            
