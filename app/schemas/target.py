"""
Schemas for targets
"""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, validator


class TargetBase(BaseModel):
    """Base schema for Target"""
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    branch_id: int
    installation_type_id: int
    target_count: int = Field(..., ge=0)
    target_days: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None


class TargetCreate(TargetBase):
    """Schema for creating a new target"""
    pass


class TargetUpdate(BaseModel):
    """Schema for updating an existing target"""
    year: Optional[int] = Field(None, ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    branch_id: Optional[int] = None
    installation_type_id: Optional[int] = None
    target_count: Optional[int] = Field(None, ge=0)
    target_days: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None


class TargetInDBBase(TargetBase):
    """Base schema for Target in DB"""
    id: int
    created_by: int
    created_at: date
    updated_at: Optional[date] = None

    class Config:
        from_attributes = True


class Target(TargetInDBBase):
    """Schema for Target response with related data"""
    branch_name: Optional[str] = None
    installation_type_name: Optional[str] = None
    created_by_name: Optional[str] = None


class TargetWithProgress(Target):
    """Schema for Target with progress information"""
    completed_count: int = 0
    completion_percentage: float = 0.0
    remaining_count: int = 0
    average_days_to_complete: Optional[float] = None
    on_time_percentage: Optional[float] = None


class TargetListResponse(BaseModel):
    """Schema for paginated target list"""
    items: List[Target]
    total: int
    page: int
    page_size: int


class TargetWithProgressListResponse(BaseModel):
    """Schema for paginated target list with progress"""
    items: List[TargetWithProgress]
    total: int
    page: int
    page_size: int 