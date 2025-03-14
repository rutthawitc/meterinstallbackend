"""
Installation Status model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.db.session import Base


class InstallationStatus(Base):
    """
    Installation Status model representing different statuses for installation requests.
    """
    __tablename__ = "installation_statuses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    installation_requests = relationship("InstallationRequest", back_populates="status")
    installation_logs = relationship("InstallationLog", back_populates="status")

    def __repr__(self):
        return f"<InstallationStatus {self.code}: {self.name}>" 