"""Job model for scheduled snapshot tasks."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class SnapshotJob(Base):
    """Represents a scheduled snapshot job for a zone."""

    __tablename__ = "snapshot_jobs"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)

    # Schedule configuration
    schedule_type = Column(String, nullable=False)  # cron, interval
    schedule_value = Column(String, nullable=False)  # cron expression or interval in seconds

    # Job status
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON, nullable=True)  # Additional job configuration

    # Relationships
    zone = relationship("Zone", back_populates="jobs")

    def __repr__(self):
        return f"<SnapshotJob(id={self.id}, zone_id={self.zone_id}, schedule='{self.schedule_type}:{self.schedule_value}')>"
