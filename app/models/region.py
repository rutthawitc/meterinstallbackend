"""
Region model for the application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.db.session import Base


class Region(Base):
    """
    Region model representing service regions.
    """
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    branches = relationship("Branch", back_populates="region")
    holidays = relationship("Holiday", back_populates="region")

    def __repr__(self):
        return f"<Region {self.code}: {self.name}>" 