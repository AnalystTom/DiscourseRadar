"""Document model for storing crawled content."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    """Document model for crawled content."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    url = Column(String(2048), nullable=False)
    title = Column(String(512), nullable=True)
    author = Column(String(255), nullable=True)
    content_markdown = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    published_at = Column(DateTime, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    job = relationship("Job", backref="documents")
