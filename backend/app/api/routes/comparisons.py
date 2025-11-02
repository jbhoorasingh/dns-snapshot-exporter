"""Comparison API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.comparison import ComparisonService
from app.api.schemas import ComparisonRequest, ComparisonResponse

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("/", response_model=ComparisonResponse)
def compare_snapshots(comparison: ComparisonRequest, db: Session = Depends(get_db)):
    """Compare two snapshots and return the differences.

    The first snapshot should typically be the older one, and the second
    the newer one, so that additions/removals are interpreted correctly.
    """
    service = ComparisonService(db)

    try:
        result = service.compare_snapshots(
            snapshot_id_1=comparison.snapshot_id_1,
            snapshot_id_2=comparison.snapshot_id_2
        )
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
