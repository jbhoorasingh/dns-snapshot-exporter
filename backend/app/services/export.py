"""Export service for exporting snapshots to various formats."""

import os
from pathlib import Path
from typing import Dict, Type
from sqlalchemy.orm import Session
from app.models import Snapshot
from app.services.snapshot import SnapshotService
from app.exporters import (
    Exporter,
    BindExporter,
    TerraformAWSExporter,
    TerraformAzureExporter,
    CSVExporter
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting snapshots to various formats."""

    # Available exporters
    EXPORTERS: Dict[str, Type[Exporter]] = {
        "bind": BindExporter,
        "terraform_aws": TerraformAWSExporter,
        "terraform_azure": TerraformAzureExporter,
        "csv": CSVExporter
    }

    def __init__(self, db: Session):
        """Initialize export service.

        Args:
            db: Database session
        """
        self.db = db
        self.snapshot_service = SnapshotService(db)

    def get_available_formats(self) -> Dict[str, str]:
        """Get available export formats.

        Returns:
            Dictionary mapping format keys to human-readable names
        """
        return {
            key: exporter().get_format_name()
            for key, exporter in self.EXPORTERS.items()
        }

    def export_snapshot(
        self,
        snapshot_id: int,
        format_key: str,
        output_path: str | None = None,
        soa_config: dict | None = None
    ) -> tuple[str, str]:
        """Export a snapshot to the specified format.

        Args:
            snapshot_id: ID of the snapshot to export
            format_key: Export format key (bind, terraform_aws, terraform_azure, csv)
            output_path: Optional output file path. If not provided, returns content only.
            soa_config: Optional SOA configuration for BIND exports

        Returns:
            Tuple of (content, file_path)
            - content: The exported content as string
            - file_path: Path to the saved file (or empty string if not saved)

        Raises:
            ValueError: If snapshot not found or format not supported
        """
        # Validate format
        if format_key not in self.EXPORTERS:
            raise ValueError(
                f"Unsupported format: {format_key}. "
                f"Available formats: {', '.join(self.EXPORTERS.keys())}"
            )

        # Get snapshot and records
        snapshot = self.snapshot_service.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        records = self.snapshot_service.get_snapshot_records(snapshot_id)

        # Create exporter and export
        exporter = self.EXPORTERS[format_key]()

        # Pass SOA config to BIND exporter if provided
        if format_key == "bind" and soa_config:
            content = exporter.export(snapshot, records, soa_config=soa_config)
        else:
            content = exporter.export(snapshot, records)

        # Save to file if output path provided
        saved_path = ""
        if output_path:
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                f.write(content)

            saved_path = output_path
            logger.info(f"Exported snapshot {snapshot_id} to {output_path}")
        else:
            # Generate default filename
            zone_name = snapshot.zone.name.rstrip('.')
            extension = exporter.get_file_extension()
            timestamp = snapshot.created_at.strftime("%Y%m%d_%H%M%S")
            filename = f"{zone_name}_{timestamp}_{format_key}{extension}"

            # Save to export directory
            export_dir = Path(settings.EXPORT_DIR)
            export_dir.mkdir(parents=True, exist_ok=True)
            saved_path = str(export_dir / filename)

            with open(saved_path, 'w') as f:
                f.write(content)

            logger.info(f"Exported snapshot {snapshot_id} to {saved_path}")

        return content, saved_path
