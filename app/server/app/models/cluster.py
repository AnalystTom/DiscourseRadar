"""Cluster model for grouping related documents."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Cluster(Base):
    """Cluster model for topic grouping."""

    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_count = Column(Integer, default=0)
    novelty_score = Column(Float, nullable=True)
    growth_rate = Column(Float, nullable=True)
    keywords = Column(JSON, nullable=True)  # List of keywords
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    job = relationship("Job", backref="clusters")
