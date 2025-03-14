"""
SLA Config model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.db.session import Base


class SLAConfig(Base):
    """
    SLA Config model for defining Service Level Agreement configurations.
    """
    __tablename__ = "sla_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    days = Column(Integer, nullable=False)  # Number of days allowed
    fee_threshold = Column(Numeric(10, 2))  # Fee threshold for this SLA
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User", back_populates="sla_configs")

    def __repr__(self):
        return f"<SLAConfig {self.name}: {self.days} days>" 