"""Infoblox WAPI connector implementation."""

import httpx
from typing import List, Dict, Any
from app.connectors.base import DNSConnector, DNSRecord
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class InfobloxConnector(DNSConnector):
    """Connector for Infoblox WAPI."""

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        wapi_version: str | None = None,
        verify_ssl: bool | None = None
    ):
        """Initialize Infoblox connector.

        Args:
            url: Infoblox server URL (defaults to settings)
            username: API username (defaults to settings)
            password: API password (defaults to settings)
            wapi_version: WAPI version (defaults to settings)
            verify_ssl: Verify SSL certificates (defaults to settings)
        """
        self.url = (url or settings.INFOBLOX_URL).rstrip('/')
        self.username = username or settings.INFOBLOX_USERNAME
        self.password = password or settings.INFOBLOX_PASSWORD
        self.wapi_version = wapi_version or settings.INFOBLOX_WAPI_VERSION
        self.verify_ssl = verify_ssl if verify_ssl is not None else settings.INFOBLOX_VERIFY_SSL

        self.base_url = f"{self.url}/wapi/{self.wapi_version}"

    def _get_client(self) -> httpx.AsyncClient:
        """Create an async HTTP client with auth."""
        return httpx.AsyncClient(
            auth=(self.username, self.password),
            verify=self.verify_ssl,
            timeout=30.0
        )

    async def test_connection(self) -> bool:
        """Test connectivity to Infoblox WAPI."""
        try:
            async with self._get_client() as client:
                response = await client.get(f"{self.base_url}/zone_auth")
                response.raise_for_status()
                logger.info("Successfully connected to Infoblox WAPI")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to Infoblox: {e}")
            raise ConnectionError(f"Failed to connect to Infoblox: {e}")

    async def get_zones(self) -> List[str]:
        """Get list of all authoritative zones from Infoblox."""
        try:
            async with self._get_client() as client:
                response = await client.get(
                    f"{self.base_url}/zone_auth",
                    params={"_return_fields": "fqdn"}
                )
                response.raise_for_status()
                zones = response.json()
                zone_names = [zone.get("fqdn") for zone in zones if zone.get("fqdn")]
                logger.info(f"Retrieved {len(zone_names)} zones from Infoblox")
                return zone_names
        except Exception as e:
            logger.error(f"Failed to get zones from Infoblox: {e}")
            raise

    async def get_zone_records(self, zone_name: str) -> tuple[List[DNSRecord], Dict[str, Any]]:
        """Get all DNS records for a specific zone from Infoblox.

        Args:
            zone_name: FQDN of the zone

        Returns:
            Tuple of (normalized_records, raw_data)
        """
        all_records = []
        raw_data = {"zone": zone_name, "record_types": {}}

        # Record types to fetch from Infoblox
        record_types = {
            "record:a": "A",
            "record:aaaa": "AAAA",
            "record:cname": "CNAME",
            "record:mx": "MX",
            "record:txt": "TXT",
            "record:ptr": "PTR",
            "record:srv": "SRV",
            "record:ns": "NS",
        }

        try:
            async with self._get_client() as client:
                for infoblox_type, record_type in record_types.items():
                    try:
                        # Build search parameters
                        params = {
                            "zone": zone_name,
                            "_return_fields+": "name,ttl,comment,disable"
                        }

                        # Add type-specific fields
                        if infoblox_type in ["record:a", "record:aaaa"]:
                            params["_return_fields+"] += ",ipv4addr" if infoblox_type == "record:a" else ",ipv6addr"
                        elif infoblox_type == "record:cname":
                            params["_return_fields+"] += ",canonical"
                        elif infoblox_type == "record:mx":
                            params["_return_fields+"] += ",mail_exchanger,preference"
                        elif infoblox_type == "record:txt":
                            params["_return_fields+"] += ",text"
                        elif infoblox_type == "record:ptr":
                            params["_return_fields+"] += ",ptrdname"
                        elif infoblox_type == "record:srv":
                            params["_return_fields+"] += ",target,port,priority,weight"
                        elif infoblox_type == "record:ns":
                            params["_return_fields+"] += ",nameserver"

                        response = await client.get(
                            f"{self.base_url}/{infoblox_type}",
                            params=params
                        )
                        response.raise_for_status()
                        records = response.json()

                        raw_data["record_types"][record_type] = records

                        # Normalize records
                        for record in records:
                            normalized = self._normalize_record(record, record_type, infoblox_type)
                            if normalized:
                                all_records.append(normalized)

                        logger.info(f"Retrieved {len(records)} {record_type} records for zone {zone_name}")

                    except httpx.HTTPStatusError as e:
                        if e.response.status_code in [404, 400]:
                            # No records of this type or not supported, which is fine
                            logger.debug(f"No {record_type} records found for zone {zone_name} (status: {e.response.status_code})")
                            continue
                        else:
                            logger.error(f"Error fetching {record_type} records: {e.response.status_code} - {e.response.text}")
                            raise

            logger.info(f"Total {len(all_records)} records retrieved for zone {zone_name}")
            return all_records, raw_data

        except Exception as e:
            logger.error(f"Failed to get records for zone {zone_name}: {e}")
            raise

    def _normalize_record(self, record: Dict[str, Any], record_type: str, infoblox_type: str) -> DNSRecord | None:
        """Normalize an Infoblox record to DNSRecord format."""
        try:
            name = record.get("name", "")
            ttl = record.get("ttl")
            comment = record.get("comment")
            disabled = record.get("disable", False)

            # Extract value based on record type
            value = None
            priority = None

            if infoblox_type == "record:a":
                value = record.get("ipv4addr")
            elif infoblox_type == "record:aaaa":
                value = record.get("ipv6addr")
            elif infoblox_type == "record:cname":
                value = record.get("canonical")
            elif infoblox_type == "record:mx":
                value = record.get("mail_exchanger")
                priority = record.get("preference")
            elif infoblox_type == "record:txt":
                value = record.get("text")
            elif infoblox_type == "record:ptr":
                value = record.get("ptrdname")
            elif infoblox_type == "record:srv":
                target = record.get("target")
                port = record.get("port")
                weight = record.get("weight")
                priority = record.get("priority")
                value = f"{weight} {port} {target}" if all([weight, port, target]) else target
            elif infoblox_type == "record:ns":
                value = record.get("nameserver")

            if not value:
                logger.warning(f"Skipping record with no value: {record}")
                return None

            return DNSRecord(
                name=name,
                record_type=record_type,
                value=value,
                ttl=ttl,
                priority=priority,
                comment=comment,
                disabled=disabled
            )

        except Exception as e:
            logger.error(f"Failed to normalize record {record}: {e}")
            return None

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "infoblox"
