"""Summary model for storing analysis results."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Summary(Base):
    """Summary model for analysis results."""

    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    summary_type = Column(String(50), nullable=False)  # cluster, topic, overall
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    key_quotes = Column(JSON, nullable=True)  # List of quotes with sources
    sentiment = Column(String(50), nullable=True)  # positive, negative, neutral, mixed
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    cluster = relationship("Cluster", backref="summaries")
    job = relationship("Job", backref="summaries")
