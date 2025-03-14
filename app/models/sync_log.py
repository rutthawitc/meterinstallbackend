"""
Sync log model for tracking synchronization with Oracle.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class SyncLog(Base):
    """
    Model for tracking synchronization with Oracle database.
    """
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=False, index=True)  # e.g., "installation_request", "holiday", etc.
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(20), nullable=False, index=True, default="running")  # running, success, failed
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)
    is_full_sync = Column(Boolean, default=False)  # True if full sync, False if delta sync
    query_params = Column(Text)  # JSON string of query parameters
    sync_details = Column(Text)  # JSON string of sync details
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="sync_logs")
    
    def __repr__(self):
        return f"<SyncLog {self.id}: {self.sync_type} - {self.status}>" 