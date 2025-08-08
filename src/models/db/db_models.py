from datetime import datetime
from src.database import Base
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, func
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

    def __repr__(self) -> str:
        return f"<Session {self.id}>"
