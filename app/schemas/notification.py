"""
Notification schemas module.
Contains all the Pydantic models for notification system.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator

# Base Notification
class NotificationBase(BaseModel):
    """Base schema for notification."""
    type: str = Field(..., description="Notification type: line, email, system, pwa_api")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    receiver: Optional[str] = Field(None, description="Notification receiver (Line Token, Email, Service ID)")
    link: Optional[str] = Field(None, description="Link to include in notification")


class NotificationCreate(NotificationBase):
    """Schema for creating notification."""
    service_id: Optional[str] = Field(None, description="Service ID for PWA API")
    ba_code: Optional[str] = Field(None, description="BA code for PWA API")


class NotificationUpdate(BaseModel):
    """Schema for updating notification."""
    is_sent: Optional[bool] = None
    sent_at: Optional[datetime] = None
    total_sent: Optional[int] = None
    success_count: Optional[int] = None
    failure_count: Optional[int] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class NotificationInDB(NotificationBase):
    """Schema for notification in database."""
    id: int
    service_id: Optional[str] = None
    ba_code: Optional[str] = None
    total_sent: int = 0
    success_count: int = 0
    failure_count: int = 0
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Notification(NotificationInDB):
    """Schema for notification response."""
    pass


# NotificationConfig schemas
class NotificationConfigBase(BaseModel):
    """Base schema for notification config."""
    name: str = Field(..., description="Configuration name")
    type: str = Field(..., description="Notification type: line, email, system, pwa_api")
    receiver: str = Field(..., description="Notification receiver (Line Token, Email, Service ID)")
    is_active: bool = Field(True, description="Whether the config is active")
    schedule: Optional[str] = Field(None, description="Schedule for notification: daily, weekly")
    config_json: Optional[Dict[str, Any]] = Field(None, description="Additional configuration in JSON")
    service_id: Optional[str] = Field(None, description="Service ID for PWA API")
    secret_key: Optional[str] = Field(None, description="Secret key for PWA API")


class NotificationConfigCreate(NotificationConfigBase):
    """Schema for creating notification config."""
    created_by: int = Field(..., description="User ID who created the config")


class NotificationConfigUpdate(BaseModel):
    """Schema for updating notification config."""
    name: Optional[str] = None
    receiver: Optional[str] = None
    is_active: Optional[bool] = None
    schedule: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    service_id: Optional[str] = None
    secret_key: Optional[str] = None


class NotificationConfigInDB(NotificationConfigBase):
    """Schema for notification config in database."""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationConfig(NotificationConfigInDB):
    """Schema for notification config response."""
    pass


# PWA Notification Target schemas
class PWANotificationTargetBase(BaseModel):
    """Base schema for PWA notification target."""
    config_id: int = Field(..., description="Notification config ID")
    ba_code: str = Field(..., description="BA code for target branch, or 'all' for all branches")
    is_active: bool = Field(True, description="Whether the target is active")


class PWANotificationTargetCreate(PWANotificationTargetBase):
    """Schema for creating PWA notification target."""
    pass


class PWANotificationTargetUpdate(BaseModel):
    """Schema for updating PWA notification target."""
    ba_code: Optional[str] = None
    is_active: Optional[bool] = None


class PWANotificationTargetInDB(PWANotificationTargetBase):
    """Schema for PWA notification target in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PWANotificationTarget(PWANotificationTargetInDB):
    """Schema for PWA notification target response."""
    pass


# PWA Notification Request schemas
class PWANotificationRequest(BaseModel):
    """Schema for PWA notification request."""
    config_id: int = Field(..., description="Notification config ID")
    message: str = Field(..., description="Notification message")
    link: Optional[str] = Field(None, description="Link to include in notification")
    ba_code: Optional[str] = Field(None, description="BA code for target branch, or 'all' for all branches")


class PWANotificationResponse(BaseModel):
    """Schema for PWA notification response."""
    success: bool
    notification_id: Optional[int] = None
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 