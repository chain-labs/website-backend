from datetime import datetime
from src.database import Base
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, func, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import text


class DBSession(Base):
    """Database model for user sessions"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    messages = relationship("MessageStore", back_populates="session")

    def __repr__(self) -> str:
        return f"<Session {self.id}>"

class MessageStore(Base):
    __tablename__ = "message_store"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String,
        ForeignKey('sessions.id', ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    # role = Column(String, nullable=False)
    # Store full LangChain message object as JSON, not plain text
    message = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    session = relationship('DBSession', back_populates="messages")

    def __repr__(self) -> str:
        return f"<MessageStore {self.id}>"
