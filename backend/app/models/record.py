"""Record model for individual DNS records."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Record(Base):
    """Represents an individual DNS record within a snapshot."""

    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False, index=True)

    # DNS record fields (normalized)
    name = Column(String, nullable=False, index=True)
    record_type = Column(String, nullable=False, index=True)  # A, AAAA, CNAME, MX, TXT, etc.
    value = Column(Text, nullable=False)
    ttl = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=True)  # For MX, SRV records

    # Additional fields for specific record types
    comment = Column(Text, nullable=True)
    disabled = Column(String, nullable=True)  # Store as string: 'true' or 'false'

    # Relationships
    snapshot = relationship("Snapshot", back_populates="records")

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_records_snapshot_type', 'snapshot_id', 'record_type'),
        Index('ix_records_snapshot_name', 'snapshot_id', 'name'),
    )

    def __repr__(self):
        return f"<Record(id={self.id}, name='{self.name}', type='{self.record_type}', value='{self.value[:50]}...')>"
