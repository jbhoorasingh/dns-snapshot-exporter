"""CSV exporter."""

import csv
from io import StringIO
from typing import List
from app.models import Record, Snapshot
from app.exporters.base import Exporter


class CSVExporter(Exporter):
    """Export DNS records to CSV format."""

    def export(self, snapshot: Snapshot, records: List[Record]) -> str:
        """Export snapshot to CSV format.

        Args:
            snapshot: Snapshot instance
            records: List of Record instances

        Returns:
            CSV content
        """
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Name",
            "Type",
            "Value",
            "TTL",
            "Priority",
            "Comment",
            "Disabled"
        ])

        # Write records
        for record in sorted(records, key=lambda r: (r.name, r.record_type)):
            writer.writerow([
                record.name,
                record.record_type,
                record.value,
                record.ttl or "",
                record.priority or "",
                record.comment or "",
                record.disabled or "false"
            ])

        return output.getvalue()

    def get_file_extension(self) -> str:
        """Get file extension."""
        return ".csv"

    def get_format_name(self) -> str:
        """Get format name."""
        return "CSV"
