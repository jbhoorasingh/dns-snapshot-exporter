"""Snapshot model for DNS zone backups."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Snapshot(Base):
    """Represents a point-in-time backup of a DNS zone."""

    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String, nullable=False)  # success, failed, in_progress
    record_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    meta_info = Column(JSON, nullable=True)  # Store provider-specific metadata
    raw_data = Column(JSON, nullable=True)  # Store raw API response for debugging

    # Relationships
    zone = relationship("Zone", back_populates="snapshots")
    records = relationship("Record", back_populates="snapshot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Snapshot(id={self.id}, zone_id={self.zone_id}, status='{self.status}', records={self.record_count})>"
