"""Pydantic schemas for Summary model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class KeyQuote(BaseModel):
    """Schema for a key quote."""
    quote: str
    source: str
    author: Optional[str] = None


class SummaryResponse(BaseModel):
    """Schema for summary response."""
    id: int
    cluster_id: Optional[int] = None
    job_id: int
    summary_type: str
    title: str
    content: str
    key_quotes: Optional[List[Dict[str, Any]]] = None
    sentiment: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
