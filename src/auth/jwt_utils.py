"""JWT utilities for token generation and validation."""

from ipaddress import ip_address
from httpx import Request
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import secrets
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.database import get_db
from src.models.db.db_models import DBSession

from ..models.auth import TokenPayload
from ..utils.errors import raise_http_error
from scripts.generate_secret import generate_jwt_secret
from src.config import JWT_SECRET_KEY, JWT_ALGORITHM, TOKEN_EXPIRY_SECONDS

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class JWTManager:
    """JWT token management."""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.expiry_seconds = TOKEN_EXPIRY_SECONDS
    
    async def generate_session_id(self, db: AsyncSession, request: Request = None) -> str:
        """Generate a unique session ID and store it in the database."""
        try:
            session_id = str(uuid.uuid4())
            print(f"Creating session with ID: {session_id}")

            # Create new session in database
            db_session = DBSession(
                id=session_id,
                user_agent=request.headers.get("user-agent") if request else None,
                ip_address=request.client.host if request and hasattr(request, "client") and request.client else None,
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                is_active=True
            )

            print(f"DB Session object created: {db_session}")
            db.add(db_session)
            print("Attempting to commit session to database...")
            
            try:
                await db.commit()
                print("Successfully committed session to database")
                await db.refresh(db_session)
                print(f"Refreshed session: {db_session}")
                return session_id
            except Exception as commit_error:
                await db.rollback()
                print(f"Error committing session to database: {str(commit_error)}")
                print(f"Error type: {type(commit_error).__name__}")
                if hasattr(commit_error, 'orig'):
                    print(f"Original error: {commit_error.orig}")
                raise
                
        except Exception as e:
            print(f"Unexpected error in generate_session_id: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'orig'):
                print(f"Original error: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create session: {str(e)}"
            )
    
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

    async def get_session(self, session_id: str, db: AsyncSession) -> Optional[DBSession]:
        """Retrieve a session from the database."""
        return await db.get(DBSession, session_id)
    
    async def update_session_activity(self, session_id: str, db: AsyncSession) -> None:
        """Update the last activity timestamp of a session."""
        session = await db.get(DBSession, session_id)
        if session:
            session.last_activity = datetime.now(timezone.utc)
            db.add(session)
            await db.commit()

    
    def get_session_id_from_token(self, token: str) -> str:
        """Extract session ID from token."""
        payload = self.decode_token(token)
        return payload.session_id


# Global JWT manager instance
jwt_manager = JWTManager()

async def get_current_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> DBSession:
    """Dependency to get current session from JWT token."""

    try:
        payload = jwt_manager.decode_token(token)
        session = await jwt_manager.get_session(payload.session_id, db)
        if not session or not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive session",
                headers={"WWW-Authenticate": "Bearer"},
            )

        await jwt_manager.update_session_activity(payload.session_id, db)
        


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
            
