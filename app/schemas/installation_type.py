"""
Installation Type schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InstallationTypeBase(BaseModel):
    """Base schema for installation type data."""
    code: str
    name: str
    description: Optional[str] = None


class InstallationTypeCreate(InstallationTypeBase):
    """Schema for creating an installation type."""
    pass


class InstallationTypeUpdate(BaseModel):
    """Schema for updating an installation type."""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class InstallationTypeInDBBase(InstallationTypeBase):
    """Schema for installation type in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class InstallationType(InstallationTypeInDBBase):
    """Schema for installation type response."""
    pass 