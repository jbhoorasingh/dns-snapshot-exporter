"""Base exporter interface."""

from abc import ABC, abstractmethod
from typing import List
from app.models import Record, Snapshot


class Exporter(ABC):
    """Abstract base class for exporters."""

    @abstractmethod
    def export(self, snapshot: Snapshot, records: List[Record]) -> str:
        """Export snapshot records to the target format.

        Args:
            snapshot: Snapshot instance
            records: List of Record instances

        Returns:
            Exported content as string
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this export format.

        Returns:
            File extension (e.g., '.zone', '.tf', '.csv')
        """
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the human-readable name of this format.

        Returns:
            Format name (e.g., 'BIND', 'Terraform AWS', 'CSV')
        """
        pass
