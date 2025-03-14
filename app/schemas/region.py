"""
Region schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RegionBase(BaseModel):
    """Base schema for region data."""
    code: str
    name: str


class RegionCreate(RegionBase):
    """Schema for creating a region."""
    pass


class RegionUpdate(BaseModel):
    """Schema for updating a region."""
    code: Optional[str] = None
    name: Optional[str] = None


class RegionInDBBase(RegionBase):
    """Schema for region in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class Region(RegionInDBBase):
    """Schema for region response."""
    pass 