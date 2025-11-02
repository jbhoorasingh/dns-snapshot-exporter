"""Snapshot API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.snapshot import SnapshotService
from app.api.schemas import SnapshotCreate, SnapshotResponse, RecordResponse

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


async def create_snapshot_task(zone_id: int, db: Session):
    """Background task to create a snapshot."""
    service = SnapshotService(db)
    await service.create_snapshot(zone_id)


@router.post("/", response_model=SnapshotResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_snapshot(
    snapshot: SnapshotCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new snapshot for a zone.

    The snapshot is created asynchronously in the background.
    Poll GET /snapshots/{id} to check status.
    """
    service = SnapshotService(db)

    # Create snapshot record immediately (will be in 'in_progress' status)
    from app.models import Snapshot, Zone

    zone = db.query(Zone).filter(Zone.id == snapshot.zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {snapshot.zone_id} not found"
        )

    # Create the snapshot asynchronously
    result = await service.create_snapshot(snapshot.zone_id)

    return result


@router.get("/zone/{zone_id}", response_model=List[SnapshotResponse])
def list_zone_snapshots(
    zone_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all snapshots for a specific zone."""
    service = SnapshotService(db)
    snapshots = service.get_snapshots_for_zone(zone_id, limit=limit)
    return snapshots


@router.get("/{snapshot_id}", response_model=SnapshotResponse)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Get a specific snapshot by ID."""
    service = SnapshotService(db)
    snapshot = service.get_snapshot_by_id(snapshot_id)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found"
        )

    return snapshot


@router.get("/{snapshot_id}/records", response_model=List[RecordResponse])
def get_snapshot_records(
    snapshot_id: int,
    record_type: str | None = None,
    db: Session = Depends(get_db)
):
    """Get all records for a specific snapshot."""
    service = SnapshotService(db)

    # Check if snapshot exists
    snapshot = service.get_snapshot_by_id(snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found"
        )

    # Get records
    records = service.get_snapshot_records(snapshot_id)

    # Filter by record type if specified
    if record_type:
        records = [r for r in records if r.record_type == record_type.upper()]

    return records


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Delete a snapshot and all its records."""
    service = SnapshotService(db)

    if not service.delete_snapshot(snapshot_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found"
        )

    return None
