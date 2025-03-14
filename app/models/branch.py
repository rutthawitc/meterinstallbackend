"""
Branch model for the application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Branch(Base):
    """
    Branch model representing service branches.
    """
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    branch_code = Column(String(20), unique=True, nullable=False, index=True)
    ba_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), index=True)
    region_code = Column(String(20), nullable=True, index=True)
    oracle_org_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="branches")
    customers = relationship("Customer", back_populates="branch")
    installation_requests = relationship("InstallationRequest", back_populates="branch")
    targets = relationship("Target", back_populates="branch")

    def __repr__(self):
        return f"<Branch {self.branch_code}: {self.name}>" 