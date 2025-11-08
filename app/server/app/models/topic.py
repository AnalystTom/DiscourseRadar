"""Topic model for tracking user-defined topics."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class Topic(Base):
    """Topic tracking model."""

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
