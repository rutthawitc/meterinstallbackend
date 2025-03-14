"""
Customer model for the application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Customer(Base):
    """
    Customer model representing service customers.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    original_id = Column(String(50), unique=True, index=True)  # ID from Oracle system
    title = Column(String(20))
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    id_card = Column(String(20))
    address = Column(Text)
    mobile = Column(String(20))
    branch_code = Column(String(20), ForeignKey("branches.ba_code"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    branch = relationship("Branch", back_populates="customers")
    installation_requests = relationship("InstallationRequest", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.id}: {self.firstname} {self.lastname}>" 