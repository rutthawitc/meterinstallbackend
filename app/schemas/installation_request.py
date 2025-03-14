"""
Schemas for installation request data validation.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, computed_field
from decimal import Decimal

# Shared properties
class InstallationRequestBase(BaseModel):
    """Base schema for installation request data."""
    request_no: str
    customer_id: Optional[int] = None
    branch_id: Optional[int] = None
    status_id: Optional[int] = None
    installation_type_id: Optional[int] = None
    meter_size_id: Optional[int] = None
    request_date: datetime
    estimated_date: Optional[datetime] = None
    approved_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    installation_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    installation_fee: Optional[Decimal] = None
    bill_no: Optional[str] = None
    remarks: Optional[str] = None
    original_req_id: Optional[str] = None
    original_install_id: Optional[str] = None
    working_days_to_estimate: Optional[int] = None
    working_days_to_payment: Optional[int] = None
    working_days_to_install: Optional[int] = None
    working_days_to_complete: Optional[int] = None
    is_exceed_sla: Optional[bool] = False
    exceed_sla_reason: Optional[str] = None

class InstallationRequestCreate(InstallationRequestBase):
    """Schema for creating a new installation request."""
    customer_id: int
    branch_id: int
    created_by: int
    status_id: int
    installation_type_id: int
    meter_size_id: int

class InstallationRequestUpdate(BaseModel):
    """Schema for updating an installation request."""
    customer_id: Optional[int] = None
    branch_id: Optional[int] = None
    status_id: Optional[int] = None
    installation_type_id: Optional[int] = None
    meter_size_id: Optional[int] = None
    estimated_date: Optional[datetime] = None
    approved_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    installation_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    installation_fee: Optional[Decimal] = None
    bill_no: Optional[str] = None
    remarks: Optional[str] = None
    working_days_to_estimate: Optional[int] = None
    working_days_to_payment: Optional[int] = None
    working_days_to_install: Optional[int] = None
    working_days_to_complete: Optional[int] = None
    is_exceed_sla: Optional[bool] = None
    exceed_sla_reason: Optional[str] = None

class InstallationRequestSchema(InstallationRequestBase):
    """Schema for installation request response."""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Define default values for relationship fields
    status_name: Optional[str] = ""
    branch_name: Optional[str] = ""
    customer_name: Optional[str] = ""
    installation_type_name: Optional[str] = ""
    meter_size_name: Optional[str] = ""
    
    class Config:
        from_attributes = True 