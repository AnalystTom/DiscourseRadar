"""Summaries router for analysis results."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.summary import Summary
from app.schemas.summary import SummaryResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("", response_model=List[SummaryResponse])
def list_summaries(
    skip: int = 0,
    limit: int = 100,
    job_id: int = None,
    cluster_id: int = None,
    summary_type: str = None,
    db: Session = Depends(get_db)
):
    """List all summaries with optional filtering."""
    query = db.query(Summary)
    if job_id:
        query = query.filter(Summary.job_id == job_id)
    if cluster_id:
        query = query.filter(Summary.cluster_id == cluster_id)
    if summary_type:
        query = query.filter(Summary.summary_type == summary_type)
    summaries = query.order_by(Summary.created_at.desc()).offset(skip).limit(limit).all()
    return summaries


@router.get("/{summary_id}", response_model=SummaryResponse)
def get_summary(summary_id: int, db: Session = Depends(get_db)):
    """Get a specific summary by ID."""
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary with id {summary_id} not found"
        )
    return summary
