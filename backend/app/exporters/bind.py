"""BIND zone file exporter."""

from typing import List, Dict
from app.models import Record, Snapshot
from app.exporters.base import Exporter
from datetime import datetime


class BindExporter(Exporter):
    """Export DNS records to BIND zone file format."""

    def export(self, snapshot: Snapshot, records: List[Record], **kwargs) -> str:
        """Export snapshot to BIND zone file format.

        Args:
            snapshot: Snapshot instance
            records: List of Record instances
            **kwargs: Additional parameters
                soa_config (Dict, optional): SOA configuration dict

        Returns:
            BIND zone file content
        """
        soa_config = kwargs.get('soa_config')
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

        # Handle SOA record first (must be at the top)
        if soa_config:
            # Use provided SOA configuration
            lines.append("; SOA Record")
            lines.append(self._format_soa_from_config(zone_name, soa_config, serial))
            lines.append("")
        elif "SOA" in records_by_type:
            # Fallback to SOA from records (if fetched from provider)
            lines.append("; SOA Record")
            soa_records = records_by_type["SOA"]
            if soa_records:
                soa_record = soa_records[0]  # Should only be one SOA record
                lines.append(self._format_soa_record(soa_record, zone_name))
                lines.append("")
            del records_by_type["SOA"]

        # Handle NS records next
        ns_names = []  # Track NS server names for A record lookup

        # Add NS from SOA config if provided
        if soa_config:
            lines.append("; NS Records")
            mname = soa_config.get("mname", "")
            lines.append(f"@{' ':29} IN NS     {mname}")
            # Store without trailing dot for A record lookup
            ns_names.append(mname.rstrip('.'))
            lines.append("")

        # Add NS records from zone data
        if "NS" in records_by_type:
            if not soa_config:  # Only add header if not already added
                lines.append("; NS Records")

            ns_records = sorted(records_by_type["NS"], key=lambda r: r.name)

            for record in ns_records:
                if record.disabled == "true":
                    lines.append(f"; DISABLED: {self._format_record(record, zone_name)}")
                else:
                    lines.append(self._format_record(record, zone_name))
                    # Extract NS server name for A record lookup
                    ns_names.append(record.value.rstrip('.'))

                if record.comment:
                    lines.append(f";   Comment: {record.comment}")

            lines.append("")
            del records_by_type["NS"]

        # Add A records for NS servers immediately after NS records (if any NS were added)
        if ns_names and "A" in records_by_type:
            lines.append("; A Records for Name Servers")
            a_records = records_by_type["A"]
            ns_a_records = []
            other_a_records = []

            # Separate NS A records from other A records
            for a_record in a_records:
                record_fqdn = a_record.name.rstrip('.')
                if any(ns_name in record_fqdn or record_fqdn in ns_name for ns_name in ns_names):
                    ns_a_records.append(a_record)
                else:
                    other_a_records.append(a_record)

            # Add NS A records
            for record in sorted(ns_a_records, key=lambda r: r.name):
                if record.disabled == "true":
                    lines.append(f"; DISABLED: {self._format_record(record, zone_name)}")
                else:
                    comment_suffix = "  ; name server" if record.comment is None else ""
                    lines.append(self._format_record(record, zone_name) + comment_suffix)

                if record.comment:
                    lines.append(f";   Comment: {record.comment}")

            lines.append("")

            # Update A records list to only contain non-NS A records
            records_by_type["A"] = other_a_records

        # Export remaining records by type
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

    def _format_soa_from_config(self, zone_name: str, soa_config: Dict, default_serial: int) -> str:
        """Format SOA record from configuration.

        Args:
            zone_name: Zone name
            soa_config: SOA configuration dict
            default_serial: Default serial number to use if not provided

        Returns:
            Formatted SOA record in multi-line format
        """
        mname = soa_config.get("mname", "ns1.example.com")
        rname = soa_config.get("rname", "admin.example.com")
        serial = soa_config.get("serial") or default_serial
        refresh = soa_config.get("refresh") or 10800
        retry = soa_config.get("retry") or 3600
        expire = soa_config.get("expire") or 2419200
        minimum = soa_config.get("minimum") or 900

        # Format as multi-line SOA record
        soa_lines = [
            f"@   IN SOA {mname} {rname} (",
            f"        {serial:10} ; serial",
            f"        {refresh:10} ; refresh",
            f"        {retry:10} ; retry",
            f"        {expire:10} ; expire",
            f"        {minimum:10} ) ; minimum"
        ]

        return "\n".join(soa_lines)

    def _format_soa_record(self, record: Record, zone_name: str) -> str:
        """Format SOA record in BIND multi-line format.

        Args:
            record: SOA Record instance
            zone_name: Zone name

        Returns:
            Formatted SOA record in multi-line format
        """
        # Parse SOA value: mname rname serial refresh retry expire minimum
        parts = record.value.split()
        if len(parts) < 7:
            # Fallback to simple format if parsing fails
            return f"@                              IN SOA    {record.value}"

        mname = parts[0]
        rname = parts[1]
        serial = parts[2]
        refresh = parts[3]
        retry = parts[4]
        expire = parts[5]
        minimum = parts[6]

        # Format as multi-line SOA record
        soa_lines = [
            f"@   IN SOA {mname} {rname} (",
            f"        {serial:10} ; serial",
            f"        {refresh:10} ; refresh",
            f"        {retry:10} ; retry",
            f"        {expire:10} ; expire",
            f"        {minimum:10} ) ; minimum"
        ]

        return "\n".join(soa_lines)

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
