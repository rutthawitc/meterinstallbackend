"""
Installation Log model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class InstallationLog(Base):
    """
    Installation Log model for tracking status changes of installation requests.
    """
    __tablename__ = "installation_logs"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("installation_requests.id"), index=True)
    status_id = Column(Integer, ForeignKey("installation_statuses.id"))
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    remarks = Column(Text)

    # Relationships
    installation_request = relationship("InstallationRequest", back_populates="installation_logs")
    status = relationship("InstallationStatus", back_populates="installation_logs")
    changed_by_user = relationship("User", back_populates="installation_logs")

    def __repr__(self):
        return f"<InstallationLog {self.id}: Installation {self.installation_id}>" 