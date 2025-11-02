"""BIND zone file exporter."""

from typing import List, Dict
from app.models import Record, Snapshot
from app.exporters.base import Exporter
from datetime import datetime


class BindExporter(Exporter):
    """Export DNS records to BIND zone file format."""

    def export(self, snapshot: Snapshot, records: List[Record]) -> str:
        """Export snapshot to BIND zone file format.

        Args:
            snapshot: Snapshot instance
            records: List of Record instances

        Returns:
            BIND zone file content
        """
        zone_name = snapshot.zone.name
        serial = int(snapshot.created_at.strftime("%Y%m%d%H"))

        # Start with zone header
        lines = [
            f"; Zone file for {zone_name}",
            f"; Generated from snapshot ID {snapshot.id}",
            f"; Created at {snapshot.created_at.isoformat()}",
            f"; Total records: {len(records)}",
            "",
            f"$ORIGIN {zone_name}.",
            "$TTL 3600",
            "",
        ]

        # Group records by type for better organization
        records_by_type: Dict[str, List[Record]] = {}
        for record in records:
            if record.record_type not in records_by_type:
                records_by_type[record.record_type] = []
            records_by_type[record.record_type].append(record)

        # Export records by type
        for record_type in sorted(records_by_type.keys()):
            lines.append(f"; {record_type} Records")
            for record in sorted(records_by_type[record_type], key=lambda r: r.name):
                # Skip disabled records with a comment
                if record.disabled == "true":
                    lines.append(f"; DISABLED: {self._format_record(record, zone_name)}")
                else:
                    lines.append(self._format_record(record, zone_name))

                # Add comment if present
                if record.comment:
                    lines.append(f";   Comment: {record.comment}")

            lines.append("")

        return "\n".join(lines)

    def _format_record(self, record: Record, zone_name: str) -> str:
        """Format a single record in BIND format.

        Args:
            record: Record instance
            zone_name: Zone name

        Returns:
            Formatted BIND record line
        """
        # Normalize name (remove zone suffix if present)
        name = record.name
        if name.endswith(f".{zone_name}"):
            name = name[:-len(zone_name)-1]
        elif name == zone_name:
            name = "@"

        # Format TTL
        ttl = record.ttl if record.ttl else ""

        # Format based on record type
        if record.record_type == "MX":
            priority = record.priority if record.priority else 10
            return f"{name:30} {ttl:6} IN {record.record_type:6} {priority} {record.value}"
        elif record.record_type == "TXT":
            # Ensure TXT records are quoted
            value = record.value if record.value.startswith('"') else f'"{record.value}"'
            return f"{name:30} {ttl:6} IN {record.record_type:6} {value}"
        elif record.record_type == "SRV":
            priority = record.priority if record.priority else 0
            return f"{name:30} {ttl:6} IN {record.record_type:6} {priority} {record.value}"
        else:
            return f"{name:30} {ttl:6} IN {record.record_type:6} {record.value}"

    def get_file_extension(self) -> str:
        """Get file extension."""
        return ".zone"

    def get_format_name(self) -> str:
        """Get format name."""
        return "BIND Zone File"
