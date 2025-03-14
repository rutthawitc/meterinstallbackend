"""
Notification model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.db.session import Base


class Notification(Base):
    """
    Notification model for tracking sent notifications.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)  # line, email, system, pwa_api
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    receiver = Column(String(255))  # Line Token, Email, Service ID
    link = Column(String(255))
    service_id = Column(String(50))  # For PWA API
    ba_code = Column(String(20))  # For PWA API
    total_sent = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    is_sent = Column(Boolean, default=False, nullable=False, index=True)
    sent_at = Column(DateTime)
    error_message = Column(Text)
    response_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id}: {self.type} - {self.title}>" 