"""Terraform Azure Private DNS exporter."""

from typing import List, Dict
from app.models import Record, Snapshot
from app.exporters.base import Exporter
import json


class TerraformAzureExporter(Exporter):
    """Export DNS records to Terraform Azure Private DNS format."""

    def export(self, snapshot: Snapshot, records: List[Record], **kwargs) -> str:
        """Export snapshot to Terraform Azure Private DNS format.

        Args:
            snapshot: Snapshot instance
            records: List of Record instances
            **kwargs: Additional parameters (unused)

        Returns:
            Terraform HCL configuration
        """
        zone_name = snapshot.zone.name

        lines = [
            f"# Terraform configuration for Azure Private DNS",
            f"# Zone: {zone_name}",
            f"# Generated from snapshot ID {snapshot.id}",
            f"# Created at {snapshot.created_at.isoformat()}",
            f"# Total records: {len(records)}",
            "",
            "# Configure the Azure Provider (uncomment and configure)",
            "# provider \"azurerm\" {",
            "#   features {}",
            "# }",
            "",
            "# Variables (uncomment and configure)",
            "# variable \"resource_group_name\" {",
            "#   description = \"Name of the resource group\"",
            "#   type        = string",
            "# }",
            "",
            f"# Azure Private DNS Zone",
            f'resource "azurerm_private_dns_zone" "{self._sanitize_name(zone_name)}" {{',
            f'  name                = "{zone_name}"',
            f'  resource_group_name = var.resource_group_name',
            f'  # tags = {{',
            f'  #   source = "infoblox-snapshot-{snapshot.id}"',
            f'  # }}',
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

        # Map record types to Azure resource types
        type_mapping = {
            "A": "azurerm_private_dns_a_record",
            "AAAA": "azurerm_private_dns_aaaa_record",
            "CNAME": "azurerm_private_dns_cname_record",
            "MX": "azurerm_private_dns_mx_record",
            "PTR": "azurerm_private_dns_ptr_record",
            "SRV": "azurerm_private_dns_srv_record",
            "TXT": "azurerm_private_dns_txt_record",
        }

        # Export each record group
        for (name, record_type), record_group in sorted(records_grouped.items()):
            if record_type not in type_mapping:
                # Skip unsupported record types with a comment
                lines.append(f"# Skipping unsupported record type: {record_type} for {name}")
                lines.append("")
                continue

            resource_type = type_mapping[record_type]
            resource_name = self._generate_resource_name(name, record_type, zone_name)

            # Get TTL (use first record's TTL or default)
            ttl = record_group[0].ttl if record_group[0].ttl else 300

            # Get record name relative to zone
            record_rel_name = self._get_relative_name(name, zone_name)

            lines.append(f'resource "{resource_type}" "{resource_name}" {{')
            lines.append(f'  name                = "{record_rel_name}"')
            lines.append(f'  zone_name           = azurerm_private_dns_zone.{self._sanitize_name(zone_name)}.name')
            lines.append(f'  resource_group_name = var.resource_group_name')
            lines.append(f'  ttl                 = {ttl}')

            # Handle records based on type
            if record_type == "A":
                values = [rec.value for rec in record_group]
                lines.append(f'  records = {json.dumps(values)}')
            elif record_type == "AAAA":
                values = [rec.value for rec in record_group]
                lines.append(f'  records = {json.dumps(values)}')
            elif record_type == "CNAME":
                # CNAME can only have one value
                lines.append(f'  record = "{record_group[0].value}"')
            elif record_type == "MX":
                # MX records need separate blocks
                for rec in record_group:
                    preference = rec.priority if rec.priority else 10
                    lines.append(f'  record {{')
                    lines.append(f'    preference = {preference}')
                    lines.append(f'    exchange   = "{rec.value}"')
                    lines.append(f'  }}')
            elif record_type == "PTR":
                values = [rec.value for rec in record_group]
                lines.append(f'  records = {json.dumps(values)}')
            elif record_type == "SRV":
                # SRV records need separate blocks with priority, weight, port, target
                for rec in record_group:
                    priority = rec.priority if rec.priority else 0
                    # Parse SRV value (format: "weight port target")
                    parts = rec.value.split()
                    if len(parts) >= 3:
                        weight, port, target = parts[0], parts[1], parts[2]
                    else:
                        weight, port, target = "0", "0", rec.value

                    lines.append(f'  record {{')
                    lines.append(f'    priority = {priority}')
                    lines.append(f'    weight   = {weight}')
                    lines.append(f'    port     = {port}')
                    lines.append(f'    target   = "{target}"')
                    lines.append(f'  }}')
            elif record_type == "TXT":
                values = [rec.value.strip('"') for rec in record_group]
                lines.append(f'  record {{')
                lines.append(f'    value = "{values[0]}"')
                lines.append(f'  }}')

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

    def _get_relative_name(self, record_name: str, zone_name: str) -> str:
        """Get record name relative to zone.

        Args:
            record_name: Full record name
            zone_name: Zone name

        Returns:
            Relative record name
        """
        if record_name.endswith(f".{zone_name}"):
            return record_name[:-len(zone_name)-1]
        elif record_name == zone_name:
            return "@"
        return record_name

    def _generate_resource_name(self, record_name: str, record_type: str, zone_name: str) -> str:
        """Generate a unique Terraform resource name.

        Args:
            record_name: DNS record name
            record_type: DNS record type
            zone_name: Zone name

        Returns:
            Sanitized resource name
        """
        rel_name = self._get_relative_name(record_name, zone_name)
        if rel_name == "@":
            rel_name = "root"

        base = self._sanitize_name(rel_name)
        return f"{base}_{record_type.lower()}" if base else f"root_{record_type.lower()}"

    def get_file_extension(self) -> str:
        """Get file extension."""
        return ".tf"

    def get_format_name(self) -> str:
        """Get format name."""
        return "Terraform Azure Private DNS"
