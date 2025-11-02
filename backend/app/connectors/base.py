"""Base connector interface for DNS providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DNSRecord:
    """Normalized DNS record structure."""
    name: str
    record_type: str
    value: str
    ttl: int | None = None
    priority: int | None = None
    comment: str | None = None
    disabled: bool = False


class DNSConnector(ABC):
    """Abstract base class for DNS provider connectors."""

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connectivity to the DNS provider.

        Returns:
            bool: True if connection is successful

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def get_zones(self) -> List[str]:
        """Get list of available DNS zones.

        Returns:
            List of zone names
        """
        pass

    @abstractmethod
    async def get_zone_records(self, zone_name: str) -> tuple[List[DNSRecord], Dict[str, Any]]:
        """Get all records for a specific zone.

        Args:
            zone_name: Name of the DNS zone

        Returns:
            Tuple of (normalized_records, raw_data)
            - normalized_records: List of DNSRecord objects
            - raw_data: Raw API response for debugging
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the DNS provider.

        Returns:
            Provider name (e.g., 'infoblox', 'route53', 'azure')
        """
        pass
