"""
Notification Config model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class NotificationConfig(Base):
    """
    Notification Config model for configuring notification settings.
    """
    __tablename__ = "notification_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, index=True)  # line, email, system, pwa_api
    receiver = Column(String(255), nullable=False)  # Line Token, Email, Service ID
    is_active = Column(Boolean, default=True, nullable=False)
    schedule = Column(String(50))  # daily, weekly
    config_json = Column(JSONB)
    service_id = Column(String(50))  # For PWA API
    secret_key = Column(String(255))  # For PWA API
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User", back_populates="notification_configs")
    pwa_notification_targets = relationship("PWANotificationTarget", back_populates="notification_config")

    def __repr__(self):
        return f"<NotificationConfig {self.id}: {self.name} ({self.type})>" 