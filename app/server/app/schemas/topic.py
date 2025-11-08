"""Pydantic schemas for Topic model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TopicBase(BaseModel):
    """Base schema for Topic."""
    name: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., min_length=1)
    description: Optional[str] = None


class TopicCreate(TopicBase):
    """Schema for creating a new topic."""
    pass


class TopicUpdate(BaseModel):
    """Schema for updating a topic."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    query: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|completed)$")


class TopicResponse(TopicBase):
    """Schema for topic response."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
