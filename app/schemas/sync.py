"""
Sync schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

from pydantic import BaseModel, Field, validator


class SyncRequest(BaseModel):
    """Schema for sync request."""
    is_full_sync: bool = True
    year: Optional[int] = None
    month: Optional[int] = None  # Added for temporary installations
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    branch_code: Optional[str] = None
    run_async: bool = False
    
    @validator("start_date", "end_date")
    def validate_date(cls, v):
        """Validate date format."""
        if v:
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("Date must be in ISO format (YYYY-MM-DD)")
        return v
    
    @validator("year")
    def validate_year(cls, v):
        """Validate year."""
        if v and (v < 1900 or v > 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return v


class SyncLogBase(BaseModel):
    """Base schema for sync log data."""
    id: int
    sync_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_failed: int = 0
    is_full_sync: bool = True
    
    class Config:
        orm_mode = True
        from_attributes = True


class SyncLogResponse(BaseModel):
    """Schema for sync log response."""
    id: Optional[int] = None
    sync_type: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    records_processed: Optional[int] = None
    records_created: Optional[int] = None
    records_updated: Optional[int] = None
    records_skipped: Optional[int] = None
    records_failed: Optional[int] = None
    message: Optional[str] = None
    is_async: bool = False


class SyncLogDetail(SyncLogBase):
    """Schema for detailed sync log response."""
    error_message: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = Field(default=None)
    sync_details: Optional[Dict[str, Any]] = Field(default=None)
    user_id: Optional[int] = None
    
    @validator("query_params", "sync_details", pre=True)
    def parse_json(cls, v):
        """Parse JSON string to dict."""
        if v and isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v 