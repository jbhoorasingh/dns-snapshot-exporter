"""Comparison service for comparing DNS snapshots."""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models import Snapshot, Record
from app.services.snapshot import SnapshotService
import logging

logger = logging.getLogger(__name__)


class ComparisonService:
    """Service for comparing DNS snapshots."""

    def __init__(self, db: Session):
        """Initialize comparison service.

        Args:
            db: Database session
        """
        self.db = db
        self.snapshot_service = SnapshotService(db)

    def _record_key(self, record: Record) -> tuple:
        """Create a unique key for a DNS record.

        Args:
            record: Record instance

        Returns:
            Tuple of (name, type, value)
        """
        return (record.name, record.record_type, record.value)

    def compare_snapshots(
        self,
        snapshot_id_1: int,
        snapshot_id_2: int
    ) -> Dict[str, Any]:
        """Compare two snapshots and return differences.

        Args:
            snapshot_id_1: ID of the first (older) snapshot
            snapshot_id_2: ID of the second (newer) snapshot

        Returns:
            Dictionary containing:
            - added: Records in snapshot_2 but not in snapshot_1
            - removed: Records in snapshot_1 but not in snapshot_2
            - modified: Records that exist in both but with different attributes
            - unchanged: Count of records that are identical

        Raises:
            ValueError: If either snapshot not found
        """
        # Get snapshots
        snapshot_1 = self.snapshot_service.get_snapshot_by_id(snapshot_id_1)
        snapshot_2 = self.snapshot_service.get_snapshot_by_id(snapshot_id_2)

        if not snapshot_1:
            raise ValueError(f"Snapshot {snapshot_id_1} not found")
        if not snapshot_2:
            raise ValueError(f"Snapshot {snapshot_id_2} not found")

        # Verify they're from the same zone
        if snapshot_1.zone_id != snapshot_2.zone_id:
            raise ValueError("Cannot compare snapshots from different zones")

        # Get records
        records_1 = self.snapshot_service.get_snapshot_records(snapshot_id_1)
        records_2 = self.snapshot_service.get_snapshot_records(snapshot_id_2)

        # Create lookup dictionaries
        records_1_dict = {self._record_key(r): r for r in records_1}
        records_2_dict = {self._record_key(r): r for r in records_2}

        keys_1 = set(records_1_dict.keys())
        keys_2 = set(records_2_dict.keys())

        # Find differences
        added_keys = keys_2 - keys_1
        removed_keys = keys_1 - keys_2
        common_keys = keys_1 & keys_2

        added = [self._record_to_dict(records_2_dict[key]) for key in added_keys]
        removed = [self._record_to_dict(records_1_dict[key]) for key in removed_keys]

        # Check for modifications in common records
        modified = []
        unchanged_count = 0

        for key in common_keys:
            r1 = records_1_dict[key]
            r2 = records_2_dict[key]

            # Compare attributes beyond the key
            changes = {}

            if r1.ttl != r2.ttl:
                changes["ttl"] = {"old": r1.ttl, "new": r2.ttl}
            if r1.priority != r2.priority:
                changes["priority"] = {"old": r1.priority, "new": r2.priority}
            if r1.comment != r2.comment:
                changes["comment"] = {"old": r1.comment, "new": r2.comment}
            if r1.disabled != r2.disabled:
                changes["disabled"] = {"old": r1.disabled, "new": r2.disabled}

            if changes:
                modified.append({
                    "record": self._record_to_dict(r2),
                    "changes": changes
                })
            else:
                unchanged_count += 1

        result = {
            "snapshot_1": {
                "id": snapshot_1.id,
                "created_at": snapshot_1.created_at.isoformat(),
                "record_count": snapshot_1.record_count
            },
            "snapshot_2": {
                "id": snapshot_2.id,
                "created_at": snapshot_2.created_at.isoformat(),
                "record_count": snapshot_2.record_count
            },
            "summary": {
                "added": len(added),
                "removed": len(removed),
                "modified": len(modified),
                "unchanged": unchanged_count
            },
            "added": added,
            "removed": removed,
            "modified": modified
        }

        logger.info(
            f"Compared snapshots {snapshot_id_1} and {snapshot_id_2}: "
            f"{len(added)} added, {len(removed)} removed, {len(modified)} modified"
        )

        return result

    def _record_to_dict(self, record: Record) -> Dict[str, Any]:
        """Convert a Record to a dictionary.

        Args:
            record: Record instance

        Returns:
            Dictionary representation
        """
        return {
            "name": record.name,
            "type": record.record_type,
            "value": record.value,
            "ttl": record.ttl,
            "priority": record.priority,
            "comment": record.comment,
            "disabled": record.disabled
        }
