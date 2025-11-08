"""Topics router for managing topic tracking."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.topic import Topic
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    """Create a new topic for tracking."""
    db_topic = Topic(
        name=topic.name,
        query=topic.query,
        description=topic.description,
        status="active"
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


@router.get("", response_model=List[TopicResponse])
def list_topics(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """List all topics with optional filtering."""
    query = db.query(Topic)
    if status_filter:
        query = query.filter(Topic.status == status_filter)
    topics = query.offset(skip).limit(limit).all()
    return topics


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get a specific topic by ID."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {topic_id} not found"
        )
    return topic


@router.patch("/{topic_id}", response_model=TopicResponse)
def update_topic(topic_id: int, topic_update: TopicUpdate, db: Session = Depends(get_db)):
    """Update a topic."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {topic_id} not found"
        )

    update_data = topic_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(topic, field, value)

    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Delete a topic."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {topic_id} not found"
        )

    db.delete(topic)
    db.commit()
    return None
