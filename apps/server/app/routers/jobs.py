"""Jobs router for managing crawl and analysis jobs."""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse, JobUpdate

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new crawl or analysis job."""
    db_job = Job(
        topic_id=job.topic_id,
        job_type=job.job_type,
        status="pending",
        progress=0
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.get("", response_model=List[JobResponse])
def list_jobs(
    skip: int = 0,
    limit: int = 100,
    topic_id: int = None,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """List all jobs with optional filtering."""
    query = db.query(Job)
    if topic_id:
        query = query.filter(Job.topic_id == topic_id)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID with status and progress."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    """Update job status and progress."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )

    update_data = job_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    # Update timestamps based on status
    if job_update.status == "running" and not job.started_at:
        job.started_at = datetime.utcnow()
    elif job_update.status in ["completed", "failed"] and not job.completed_at:
        job.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/rerun", response_model=JobResponse)
def rerun_job(job_id: int, db: Session = Depends(get_db)):
    """Re-run a completed or failed job."""
    original_job = db.query(Job).filter(Job.id == job_id).first()
    if not original_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )

    # Create a new job based on the original
    new_job = Job(
        topic_id=original_job.topic_id,
        job_type=original_job.job_type,
        status="pending",
        progress=0,
        job_metadata=original_job.job_metadata
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job
