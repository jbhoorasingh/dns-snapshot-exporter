"""Snapshot job API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import SnapshotJob, Zone
from app.api.schemas import JobCreate, JobUpdate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new scheduled snapshot job."""
    # Validate zone exists
    zone = db.query(Zone).filter(Zone.id == job.zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {job.zone_id} not found"
        )

    # Validate schedule type
    if job.schedule_type not in ["cron", "interval"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="schedule_type must be 'cron' or 'interval'"
        )

    # Create job
    db_job = SnapshotJob(
        zone_id=job.zone_id,
        schedule_type=job.schedule_type,
        schedule_value=job.schedule_value,
        enabled=job.enabled
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job


@router.get("/", response_model=List[JobResponse])
def list_jobs(
    zone_id: int | None = None,
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all scheduled snapshot jobs."""
    query = db.query(SnapshotJob)

    if zone_id is not None:
        query = query.filter(SnapshotJob.zone_id == zone_id)

    if enabled_only:
        query = query.filter(SnapshotJob.enabled == True)

    jobs = query.all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID."""
    job = db.query(SnapshotJob).filter(SnapshotJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    """Update a scheduled job."""
    job = db.query(SnapshotJob).filter(SnapshotJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Update fields
    if job_update.schedule_type is not None:
        if job_update.schedule_type not in ["cron", "interval"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="schedule_type must be 'cron' or 'interval'"
            )
        job.schedule_type = job_update.schedule_type

    if job_update.schedule_value is not None:
        job.schedule_value = job_update.schedule_value

    if job_update.enabled is not None:
        job.enabled = job_update.enabled

    db.commit()
    db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a scheduled job."""
    job = db.query(SnapshotJob).filter(SnapshotJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    db.delete(job)
    db.commit()

    return None
