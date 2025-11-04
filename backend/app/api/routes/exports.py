"""Export API routes."""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.export import ExportService
from app.api.schemas import ExportRequest, ExportResponse

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/formats", response_model=Dict[str, str])
def get_export_formats(db: Session = Depends(get_db)):
    """Get available export formats."""
    service = ExportService(db)
    return service.get_available_formats()


@router.post("/", response_model=ExportResponse)
def export_snapshot(export_req: ExportRequest, db: Session = Depends(get_db)):
    """Export a snapshot to the specified format.

    Returns the exported content and the path where it was saved.
    """
    service = ExportService(db)

    try:
        # Convert SOA config to dict if provided
        soa_config = export_req.soa_config.model_dump() if export_req.soa_config else None

        content, file_path = service.export_snapshot(
            snapshot_id=export_req.snapshot_id,
            format_key=export_req.format,
            soa_config=soa_config
        )

        return ExportResponse(
            content=content,
            file_path=file_path,
            format=export_req.format
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/download")
def download_export(export_req: ExportRequest, db: Session = Depends(get_db)):
    """Export a snapshot and return it as a downloadable file."""
    service = ExportService(db)

    try:
        # Convert SOA config to dict if provided
        soa_config = export_req.soa_config.model_dump() if export_req.soa_config else None

        content, _ = service.export_snapshot(
            snapshot_id=export_req.snapshot_id,
            format_key=export_req.format,
            soa_config=soa_config
        )

        # Get file extension
        exporter_class = service.EXPORTERS[export_req.format]
        exporter = exporter_class()
        extension = exporter.get_file_extension()

        # Get snapshot for filename
        snapshot = service.snapshot_service.get_snapshot_by_id(export_req.snapshot_id)
        zone_name = snapshot.zone.name.rstrip('.')
        timestamp = snapshot.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{zone_name}_{timestamp}_{export_req.format}{extension}"

        # Determine media type
        media_type_map = {
            ".zone": "text/plain",
            ".tf": "text/plain",
            ".csv": "text/csv"
        }
        media_type = media_type_map.get(extension, "text/plain")

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
