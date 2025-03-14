"""
Installation Status schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InstallationStatusBase(BaseModel):
    """Base schema for installation status data."""
    code: str
    name: str
    description: Optional[str] = None


class InstallationStatusCreate(InstallationStatusBase):
    """Schema for creating an installation status."""
    pass


class InstallationStatusUpdate(BaseModel):
    """Schema for updating an installation status."""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class InstallationStatusInDBBase(InstallationStatusBase):
    """Schema for installation status in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class InstallationStatus(InstallationStatusInDBBase):
    """Schema for installation status response."""
    pass 