"""
Meter Size schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MeterSizeBase(BaseModel):
    """Base schema for meter size data."""
    code: str
    name: str
    description: Optional[str] = None


class MeterSizeCreate(MeterSizeBase):
    """Schema for creating a meter size."""
    pass


class MeterSizeUpdate(BaseModel):
    """Schema for updating a meter size."""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class MeterSizeInDBBase(MeterSizeBase):
    """Schema for meter size in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class MeterSize(MeterSizeInDBBase):
    """Schema for meter size response."""
    pass 