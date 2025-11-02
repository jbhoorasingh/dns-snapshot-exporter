"""Snapshot service for creating and managing DNS zone snapshots."""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.models import Zone, Snapshot, Record
from app.connectors import DNSConnector, InfobloxConnector
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for creating and managing DNS snapshots."""

    def __init__(self, db: Session):
        """Initialize snapshot service.

        Args:
            db: Database session
        """
        self.db = db

    def get_connector_for_zone(self, zone: Zone) -> DNSConnector:
        """Get the appropriate connector for a zone based on its provider.

        Args:
            zone: Zone model instance

        Returns:
            DNSConnector instance

        Raises:
            ValueError: If provider is not supported
        """
        if zone.provider.lower() == "infoblox":
            return InfobloxConnector()
        # Future: Add other providers here
        # elif zone.provider.lower() == "route53":
        #     return Route53Connector()
        # elif zone.provider.lower() == "azure":
        #     return AzureConnector()
        else:
            raise ValueError(f"Unsupported provider: {zone.provider}")

    async def create_snapshot(self, zone_id: int) -> Snapshot:
        """Create a new snapshot for a zone.

        Args:
            zone_id: ID of the zone to snapshot

        Returns:
            Created Snapshot instance

        Raises:
            ValueError: If zone not found
        """
        # Get zone
        zone = self.db.query(Zone).filter(Zone.id == zone_id).first()
        if not zone:
            raise ValueError(f"Zone with ID {zone_id} not found")

        # Create snapshot record
        snapshot = Snapshot(
            zone_id=zone_id,
            status="in_progress",
            created_at=datetime.utcnow()
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        try:
            logger.info(f"Starting snapshot for zone {zone.name} (ID: {zone_id})")

            # Get connector
            connector = self.get_connector_for_zone(zone)

            # Fetch records from provider
            dns_records, raw_data = await connector.get_zone_records(zone.name)

            # Store records in database
            record_count = 0
            for dns_record in dns_records:
                record = Record(
                    snapshot_id=snapshot.id,
                    name=dns_record.name,
                    record_type=dns_record.record_type,
                    value=dns_record.value,
                    ttl=dns_record.ttl,
                    priority=dns_record.priority,
                    comment=dns_record.comment,
                    disabled=str(dns_record.disabled).lower() if dns_record.disabled is not None else None
                )
                self.db.add(record)
                record_count += 1

            # Update snapshot status
            snapshot.status = "success"
            snapshot.record_count = record_count
            snapshot.raw_data = raw_data
            snapshot.meta_info = {
                "provider": zone.provider,
                "zone_name": zone.name
            }

            self.db.commit()
            self.db.refresh(snapshot)

            logger.info(f"Snapshot completed for zone {zone.name}: {record_count} records")
            return snapshot

        except Exception as e:
            logger.error(f"Snapshot failed for zone {zone.name}: {e}")
            snapshot.status = "failed"
            snapshot.error_message = str(e)
            self.db.commit()
            self.db.refresh(snapshot)
            raise

    def get_snapshots_for_zone(self, zone_id: int, limit: int = 100) -> List[Snapshot]:
        """Get snapshots for a specific zone.

        Args:
            zone_id: ID of the zone
            limit: Maximum number of snapshots to return

        Returns:
            List of Snapshot instances
        """
        snapshots = (
            self.db.query(Snapshot)
            .filter(Snapshot.zone_id == zone_id)
            .order_by(Snapshot.created_at.desc())
            .limit(limit)
            .all()
        )
        return snapshots

    def get_snapshot_by_id(self, snapshot_id: int) -> Snapshot | None:
        """Get a specific snapshot by ID.

        Args:
            snapshot_id: ID of the snapshot

        Returns:
            Snapshot instance or None
        """
        return self.db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()

    def get_snapshot_records(self, snapshot_id: int) -> List[Record]:
        """Get all records for a specific snapshot.

        Args:
            snapshot_id: ID of the snapshot

        Returns:
            List of Record instances
        """
        records = (
            self.db.query(Record)
            .filter(Record.snapshot_id == snapshot_id)
            .order_by(Record.name, Record.record_type)
            .all()
        )
        return records

    def delete_snapshot(self, snapshot_id: int) -> bool:
        """Delete a snapshot and its records.

        Args:
            snapshot_id: ID of the snapshot to delete

        Returns:
            True if deleted, False if not found
        """
        snapshot = self.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            return False

        self.db.delete(snapshot)
        self.db.commit()
        logger.info(f"Deleted snapshot {snapshot_id}")
        return True
