"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Zone schemas
class ZoneCreate(BaseModel):
    """Schema for creating a zone."""
    name: str = Field(..., description="DNS zone name (e.g., example.com)")
    description: Optional[str] = Field(None, description="Zone description")
    provider: str = Field(..., description="DNS provider (e.g., infoblox)")
    enabled: bool = Field(True, description="Whether the zone is enabled")


class ZoneUpdate(BaseModel):
    """Schema for updating a zone."""
    description: Optional[str] = None
    enabled: Optional[bool] = None


class ZoneResponse(BaseModel):
    """Schema for zone response."""
    id: int
    name: str
    description: Optional[str]
    provider: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Snapshot schemas
class SnapshotCreate(BaseModel):
    """Schema for creating a snapshot."""
    zone_id: int = Field(..., description="ID of the zone to snapshot")


class SnapshotResponse(BaseModel):
    """Schema for snapshot response."""
    id: int
    zone_id: int
    created_at: datetime
    status: str
    record_count: int
    error_message: Optional[str]
    meta_info: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# Record schemas
class RecordResponse(BaseModel):
    """Schema for DNS record response."""
    id: int
    snapshot_id: int
    name: str
    record_type: str
    value: str
    ttl: Optional[int]
    priority: Optional[int]
    comment: Optional[str]
    disabled: Optional[str]

    class Config:
        from_attributes = True


# Export schemas
class SOAConfig(BaseModel):
    """Schema for SOA record configuration."""
    mname: str = Field(..., description="Primary nameserver (e.g., ns1.example.com)")
    rname: str = Field(..., description="Email address (e.g., admin.example.com)")
    serial: Optional[int] = Field(None, description="Serial number (auto-generated if not provided)")
    refresh: int = Field(10800, description="Refresh interval in seconds")
    retry: int = Field(3600, description="Retry interval in seconds")
    expire: int = Field(2419200, description="Expire time in seconds")
    minimum: int = Field(900, description="Negative caching TTL in seconds")
    ttl: int = Field(3600, description="Default TTL for the zone")


class ExportRequest(BaseModel):
    """Schema for export request."""
    snapshot_id: int = Field(..., description="ID of the snapshot to export")
    format: str = Field(..., description="Export format (bind, terraform_aws, terraform_azure, csv)")
    soa_config: Optional[SOAConfig] = Field(None, description="SOA configuration for BIND exports")


class ExportResponse(BaseModel):
    """Schema for export response."""
    content: str = Field(..., description="Exported content")
    file_path: str = Field(..., description="Path to saved file")
    format: str = Field(..., description="Export format used")


# Comparison schemas
class ComparisonRequest(BaseModel):
    """Schema for comparison request."""
    snapshot_id_1: int = Field(..., description="ID of the first (older) snapshot")
    snapshot_id_2: int = Field(..., description="ID of the second (newer) snapshot")


class RecordChange(BaseModel):
    """Schema for a single record in comparison."""
    name: str
    type: str
    value: str
    ttl: Optional[int]
    priority: Optional[int]
    comment: Optional[str]
    disabled: Optional[str]


class RecordModification(BaseModel):
    """Schema for a modified record."""
    record: RecordChange
    changes: Dict[str, Dict[str, Any]]


class ComparisonSummary(BaseModel):
    """Schema for comparison summary."""
    added: int
    removed: int
    modified: int
    unchanged: int


class SnapshotInfo(BaseModel):
    """Schema for snapshot info in comparison."""
    id: int
    created_at: str
    record_count: int


class ComparisonResponse(BaseModel):
    """Schema for comparison response."""
    snapshot_1: SnapshotInfo
    snapshot_2: SnapshotInfo
    summary: ComparisonSummary
    added: List[RecordChange]
    removed: List[RecordChange]
    modified: List[RecordModification]


# Job schemas
class JobCreate(BaseModel):
    """Schema for creating a snapshot job."""
    zone_id: int = Field(..., description="ID of the zone to snapshot")
    schedule_type: str = Field(..., description="Schedule type (cron or interval)")
    schedule_value: str = Field(..., description="Cron expression or interval in seconds")
    enabled: bool = Field(True, description="Whether the job is enabled")


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    schedule_type: Optional[str] = None
    schedule_value: Optional[str] = None
    enabled: Optional[bool] = None


class JobResponse(BaseModel):
    """Schema for job response."""
    id: int
    zone_id: int
    schedule_type: str
    schedule_value: str
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Health check schema
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
