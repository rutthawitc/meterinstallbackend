"""
Installation Type model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.db.session import Base


class InstallationType(Base):
    """
    Installation Type model representing different types of installation.
    """
    __tablename__ = "installation_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    installation_requests = relationship("InstallationRequest", back_populates="installation_type")
    targets = relationship("Target", back_populates="installation_type")

    def __repr__(self):
        return f"<InstallationType {self.code}: {self.name}>" 