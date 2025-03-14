"""
Branch schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.region import Region


class BranchBase(BaseModel):
    """Base schema for branch data."""
    branch_code: str
    ba_code: str
    name: str
    region_id: int
    region_code: Optional[str] = None
    oracle_org_id: Optional[str] = None


class BranchCreate(BranchBase):
    """Schema for creating a branch."""
    pass


class BranchUpdate(BaseModel):
    """Schema for updating a branch."""
    branch_code: Optional[str] = None
    ba_code: Optional[str] = None
    name: Optional[str] = None
    region_id: Optional[int] = None
    region_code: Optional[str] = None
    oracle_org_id: Optional[str] = None


class BranchInDBBase(BranchBase):
    """Schema for branch in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class Branch(BranchInDBBase):
    """Schema for branch response."""
    pass


class BranchWithRegion(Branch):
    """Schema for branch response with region data."""
    region: Optional[Region] = None 