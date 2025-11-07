"""Pydantic schemas for Job model."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class JobBase(BaseModel):
    """Base schema for Job."""
    job_type: str = Field(..., pattern="^(crawl|analysis|full)$")
    topic_id: Optional[int] = None


class JobCreate(JobBase):
    """Schema for creating a new job."""
    pass


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed)$")
    progress: Optional[int] = Field(None, ge=0, le=100)
    job_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class JobResponse(JobBase):
    """Schema for job response."""
    id: int
    status: str
    progress: int
    job_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
