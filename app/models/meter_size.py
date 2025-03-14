"""
Meter Size model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.db.session import Base


class MeterSize(Base):
    """
    Meter Size model representing different sizes of water meters.
    """
    __tablename__ = "meter_sizes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    installation_requests = relationship("InstallationRequest", back_populates="meter_size")

    def __repr__(self):
        return f"<MeterSize {self.code}: {self.name}>" 