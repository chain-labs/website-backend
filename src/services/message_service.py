"""Service for managing messages."""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db.db_models import Message


class MessageService:
    """Service for managing messages."""
    

    @staticmethod
    async def log_message(
        db: AsyncSession,
        session_id: str,
        endpoint: str,
        role: str,
        content: str
    ) -> Message:
        """
        Log a message to the database.

        Args:
            db: Database session
            session_id: The session ID to associate with this message
            endpoint: The API endpoint that generated this message (e.g., "/api/goal")
            role: The role of the message sender ("user" or "assistant")
            content: The message content

        Returns:
            The logged message object
        
        """

        message = Message(
            session_id=session_id,
            endpoint=endpoint,
            role=role,
            content=content
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        return message
    

    @staticmethod
    async def get_session_messages(
        db: AsyncSession,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[Message]:
        """
        Retrieve messages for a specific session.
        
        Args:
            db: Database session
            session_id: The session ID to retrieve messages for
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of Message objects
        """

        from sqlalchemy import select
        
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.timestamp.asc())
            .offset(offset)
            .limit(limit)
        )
        
        return result.scalars().all()
