"""
Installation Request model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.db.session import Base


class InstallationRequest(Base):
    """
    Installation Request model representing meter installation requests.
    """
    __tablename__ = "installation_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_code = Column(String(20), ForeignKey("branches.ba_code", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status_id = Column(Integer, ForeignKey("installation_statuses.id", ondelete="SET NULL"), nullable=True, index=True)
    installation_type_id = Column(Integer, ForeignKey("installation_types.id", ondelete="SET NULL"), nullable=True)
    meter_size_id = Column(Integer, ForeignKey("meter_sizes.id", ondelete="SET NULL"), nullable=True)
    request_date = Column(DateTime, nullable=True, index=True)  # Changed to nullable=True
    estimated_date = Column(DateTime)
    approved_date = Column(DateTime)
    payment_date = Column(DateTime)
    installation_date = Column(DateTime)
    completion_date = Column(DateTime)
    installation_fee = Column(Numeric(10, 2))
    bill_no = Column(String(50))
    remarks = Column(Text)
    original_req_id = Column(String(50))
    original_install_id = Column(String(50))
    working_days_to_estimate = Column(Integer)
    working_days_to_payment = Column(Integer)
    working_days_to_install = Column(Integer)
    working_days_to_complete = Column(Integer)
    is_exceed_sla = Column(Boolean, default=False)
    exceed_sla_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="installation_requests")
    branch = relationship("Branch", back_populates="installation_requests")
    created_by_user = relationship("User", back_populates="installation_requests")
    status = relationship("InstallationStatus", back_populates="installation_requests")
    installation_type = relationship("InstallationType", back_populates="installation_requests")
    meter_size = relationship("MeterSize", back_populates="installation_requests")
    installation_logs = relationship("InstallationLog", back_populates="installation_request")

    def __repr__(self):
        return f"<InstallationRequest {self.request_no}>" 