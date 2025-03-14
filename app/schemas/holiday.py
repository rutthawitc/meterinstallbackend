"""
Schemas for holidays.
"""
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class HolidayBase(BaseModel):
    """Base schema for holidays."""
    holiday_date: date = Field(..., description="Date of the holiday")
    description: str = Field(..., description="Description of the holiday")
    is_national_holiday: bool = Field(True, description="Whether this is a national holiday")
    is_repeating_yearly: bool = Field(False, description="Whether this holiday repeats yearly")
    region_id: Optional[int] = Field(None, description="ID of the region (optional, NULL for nationwide holidays)")


class HolidayCreate(HolidayBase):
    """Schema for creating holidays."""
    pass


class HolidayUpdate(BaseModel):
    """Schema for updating holidays."""
    holiday_date: Optional[date] = Field(None, description="Date of the holiday")
    description: Optional[str] = Field(None, description="Description of the holiday")
    is_national_holiday: Optional[bool] = Field(None, description="Whether this is a national holiday")
    is_repeating_yearly: Optional[bool] = Field(None, description="Whether this holiday repeats yearly")
    region_id: Optional[int] = Field(None, description="ID of the region (optional, NULL for nationwide holidays)")


class HolidayResponse(HolidayBase):
    """Schema for holiday responses."""
    id: int
    original_id: Optional[str] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
