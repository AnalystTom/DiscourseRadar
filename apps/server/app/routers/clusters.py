"""Clusters router for topic groupings."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cluster import Cluster
from app.schemas.cluster import ClusterResponse

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=List[ClusterResponse])
def list_clusters(
    skip: int = 0,
    limit: int = 100,
    job_id: int = None,
    db: Session = Depends(get_db)
):
    """List all clusters with optional filtering by job."""
    query = db.query(Cluster)
    if job_id:
        query = query.filter(Cluster.job_id == job_id)
    clusters = query.order_by(Cluster.novelty_score.desc()).offset(skip).limit(limit).all()
    return clusters


@router.get("/{cluster_id}", response_model=ClusterResponse)
def get_cluster(cluster_id: int, db: Session = Depends(get_db)):
    """Get a specific cluster by ID."""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster with id {cluster_id} not found"
        )
    return cluster


@router.get("/job/{job_id}/emerging", response_model=List[ClusterResponse])
def get_emerging_clusters(job_id: int, threshold: float = 0.75, db: Session = Depends(get_db)):
    """Get emerging clusters for a job based on novelty threshold."""
    clusters = (
        db.query(Cluster)
        .filter(Cluster.job_id == job_id)
        .filter(Cluster.novelty_score >= threshold)
        .order_by(Cluster.novelty_score.desc())
        .all()
    )
    return clusters
