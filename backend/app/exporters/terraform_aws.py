"""Terraform AWS Route 53 exporter."""

from typing import List, Dict
from app.models import Record, Snapshot
from app.exporters.base import Exporter
import json


class TerraformAWSExporter(Exporter):
    """Export DNS records to Terraform AWS Route 53 format."""

    def export(self, snapshot: Snapshot, records: List[Record], **kwargs) -> str:
        """Export snapshot to Terraform AWS Route 53 format.

        Args:
            snapshot: Snapshot instance
            records: List of Record instances
            **kwargs: Additional parameters (unused)

        Returns:
            Terraform HCL configuration
        """
        zone_name = snapshot.zone.name

        lines = [
            f"# Terraform configuration for AWS Route 53",
            f"# Zone: {zone_name}",
            f"# Generated from snapshot ID {snapshot.id}",
            f"# Created at {snapshot.created_at.isoformat()}",
            f"# Total records: {len(records)}",
            "",
            "# Configure the AWS Provider (uncomment and configure)",
            "# provider \"aws\" {",
            "#   region = \"us-east-1\"",
            "# }",
            "",
            f"# Route 53 Hosted Zone",
            f'resource "aws_route53_zone" "{self._sanitize_name(zone_name)}" {{',
            f'  name = "{zone_name}"',
            f'  comment = "Imported from Infoblox snapshot {snapshot.id}"',
            "}",
            "",
        ]

        # Group records by (name, type) for multi-value records
        records_grouped: Dict[tuple, List[Record]] = {}
        for record in records:
            # Skip disabled records
            if record.disabled == "true":
                continue

            key = (record.name, record.record_type)
            if key not in records_grouped:
                records_grouped[key] = []
            records_grouped[key].append(record)

        # Export each record group
        for (name, record_type), record_group in sorted(records_grouped.items()):
            resource_name = self._generate_resource_name(name, record_type, zone_name)

            # Get TTL (use first record's TTL or default)
            ttl = record_group[0].ttl if record_group[0].ttl else 300

            lines.append(f'resource "aws_route53_record" "{resource_name}" {{')
            lines.append(f'  zone_id = aws_route53_zone.{self._sanitize_name(zone_name)}.zone_id')
            lines.append(f'  name    = "{name}"')
            lines.append(f'  type    = "{record_type}"')
            lines.append(f'  ttl     = {ttl}')

            # Handle records based on type
            if record_type == "MX":
                # MX records need priority included in value
                values = []
                for rec in record_group:
                    priority = rec.priority if rec.priority else 10
                    values.append(f'"{priority} {rec.value}"')
                lines.append(f'  records = [{", ".join(values)}]')
            elif record_type == "TXT":
                # TXT records need proper escaping
                values = []
                for rec in record_group:
                    # Escape quotes and ensure proper formatting
                    txt_value = rec.value.replace('"', '\\"')
                    if not txt_value.startswith('"'):
                        txt_value = f'"{txt_value}"'
                    values.append(txt_value)
                lines.append(f'  records = [{", ".join(values)}]')
            elif record_type == "SRV":
                # SRV records need priority, weight, port, and target
                values = []
                for rec in record_group:
                    priority = rec.priority if rec.priority else 0
                    values.append(f'"{priority} {rec.value}"')
                lines.append(f'  records = [{", ".join(values)}]')
            else:
                # Standard records (A, AAAA, CNAME, NS, etc.)
                values = [f'"{rec.value}"' for rec in record_group]
                lines.append(f'  records = [{", ".join(values)}]')

            # Add comment if present
            if record_group[0].comment:
                comment = record_group[0].comment.replace('"', '\\"')
                lines.append(f'  # Comment: {comment}')

            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use as Terraform resource identifier.

        Args:
            name: Original name

        Returns:
            Sanitized name
        """
        return name.replace(".", "_").replace("-", "_").rstrip("_")

    def _generate_resource_name(self, record_name: str, record_type: str, zone_name: str) -> str:
        """Generate a unique Terraform resource name.

        Args:
            record_name: DNS record name
            record_type: DNS record type
            zone_name: Zone name

        Returns:
            Sanitized resource name
        """
        # Remove zone suffix
        if record_name.endswith(f".{zone_name}"):
            record_name = record_name[:-len(zone_name)-1]
        elif record_name == zone_name:
            record_name = "root"

        base = self._sanitize_name(record_name)
        return f"{base}_{record_type.lower()}" if base else f"root_{record_type.lower()}"

    def get_file_extension(self) -> str:
        """Get file extension."""
        return ".tf"

    def get_format_name(self) -> str:
        """Get format name."""
        return "Terraform AWS Route 53"
