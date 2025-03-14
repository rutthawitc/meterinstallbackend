"""
Holiday model.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base


class Holiday(Base):
    """
    Holiday model to store official holidays and special off days.
    """
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    holiday_date = Column(Date, nullable=False, index=True, unique=True)
    description = Column(String(255), nullable=False)
    is_national_holiday = Column(Boolean, default=True)  # True for national holidays, False for regional or special off days
    is_repeating_yearly = Column(Boolean, default=False)  # True for holidays that repeat every year (e.g., New Year)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)  # NULL for nationwide holidays
    original_id = Column(String(50), nullable=True)  # ID from Oracle database
    updated_by = Column(Integer, ForeignKey("users.id"))  # User who last updated this record
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    region = relationship("Region", back_populates="holidays")
    updated_by_user = relationship("User", back_populates="holidays")
    
    def __repr__(self):
        return f"<Holiday {self.holiday_date}: {self.description}>" 