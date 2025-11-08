"""Pydantic schemas for Document model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, ConfigDict


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    job_id: int
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    content_markdown: Optional[str] = None
    sentiment_score: Optional[float] = None
    published_at: Optional[datetime] = None
    crawled_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
