import datetime
from src.database import Base
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class DBSession(Base):
    """Database model for user sessions"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(datetime(timezone=True), server_default=func.now())
    last_activity = Column(datetime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Session {self.id}>"

class Message(Base):
    """Database model for chat messages"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(datetime(timezone=True), server_default=func.now())

    session = relationship("DBSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.id} from session {self.session_id}>"