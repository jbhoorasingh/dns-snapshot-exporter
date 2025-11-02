"""Zone model for DNS zones to be backed up."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Zone(Base):
    """Represents a DNS zone to be backed up."""

    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    provider = Column(String, nullable=False)  # infoblox, route53, azure, etc.
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    snapshots = relationship("Snapshot", back_populates="zone", cascade="all, delete-orphan")
    jobs = relationship("SnapshotJob", back_populates="zone", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Zone(id={self.id}, name='{self.name}', provider='{self.provider}')>"
