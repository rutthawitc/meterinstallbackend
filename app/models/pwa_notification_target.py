"""
PWA Notification Target model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class PWANotificationTarget(Base):
    """
    PWA Notification Target model for configuring PWA API notification targets.
    """
    __tablename__ = "pwa_notification_targets"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("notification_configs.id"), index=True)
    ba_code = Column(String(20), nullable=False, index=True)  # Branch code or 'all'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    notification_config = relationship("NotificationConfig", back_populates="pwa_notification_targets")

    def __repr__(self):
        return f"<PWANotificationTarget {self.id}: {self.ba_code}>" 