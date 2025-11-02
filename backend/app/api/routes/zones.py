"""Zone management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Zone
from app.api.schemas import ZoneCreate, ZoneUpdate, ZoneResponse

router = APIRouter(prefix="/zones", tags=["zones"])


@router.post("/", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(zone: ZoneCreate, db: Session = Depends(get_db)):
    """Create a new DNS zone to track."""
    # Check if zone already exists
    existing = db.query(Zone).filter(Zone.name == zone.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone {zone.name} already exists"
        )

    # Create zone
    db_zone = Zone(
        name=zone.name,
        description=zone.description,
        provider=zone.provider,
        enabled=zone.enabled
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)

    return db_zone


@router.get("/", response_model=List[ZoneResponse])
def list_zones(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all DNS zones."""
    query = db.query(Zone)

    if enabled_only:
        query = query.filter(Zone.enabled == True)

    zones = query.offset(skip).limit(limit).all()
    return zones


@router.get("/{zone_id}", response_model=ZoneResponse)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    """Get a specific zone by ID."""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )
    return zone


@router.patch("/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: int, zone_update: ZoneUpdate, db: Session = Depends(get_db)):
    """Update a zone."""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )

    # Update fields
    if zone_update.description is not None:
        zone.description = zone_update.description
    if zone_update.enabled is not None:
        zone.enabled = zone_update.enabled

    db.commit()
    db.refresh(zone)

    return zone


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    """Delete a zone and all its snapshots."""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )

    db.delete(zone)
    db.commit()

    return None
