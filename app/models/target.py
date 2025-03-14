"""
Target model for installation targets
"""
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base

class Target(Base):
    """
    Target model for installation targets.
    """
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    branch_code = Column(String(20), ForeignKey("branches.ba_code"), nullable=False)
    installation_type_id = Column(Integer, ForeignKey("installation_types.id"), nullable=False)
    target_count = Column(Integer, nullable=False)
    target_days = Column(Integer, nullable=True, comment="Target days to complete installation")
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(Date, default=datetime.utcnow)
    updated_at = Column(Date, nullable=True)

    # Relationships
    branch = relationship("Branch", back_populates="targets")
    installation_type = relationship("InstallationType", back_populates="targets")
    created_by_user = relationship("User", backref="created_targets")

    # Add unique constraint for year+month+branch+installation_type
    __table_args__ = (
        UniqueConstraint('year', 'month', 'branch_code', 'installation_type_id', name='unique_target'),
    )
    
    def __repr__(self):
        return f"<Target year={self.year} month={self.month} branch_code={self.branch_code} target_count={self.target_count}>" 