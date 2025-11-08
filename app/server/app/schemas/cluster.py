"""Pydantic schemas for Cluster model."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ClusterResponse(BaseModel):
    """Schema for cluster response."""
    id: int
    job_id: int
    name: str
    description: Optional[str] = None
    document_count: int
    novelty_score: Optional[float] = None
    growth_rate: Optional[float] = None
    keywords: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
