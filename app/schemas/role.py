"""
Role schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional, List, Any, Dict, Union, ForwardRef

from pydantic import BaseModel, Field

# Use string annotations to avoid circular imports
# UserBasic = ForwardRef('UserBasic')

class RoleBase(BaseModel):
    """Base schema for role data."""
    name: str
    description: Optional[str] = None
    is_default: bool = False
    permissions: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a role."""
    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    permissions: Optional[str] = None


class RoleInDBBase(RoleBase):
    """Schema for role in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class Role(RoleInDBBase):
    """Schema for role response."""
    pass


class RoleWithUsers(Role):
    """Schema for role response with user data."""
    # Use string annotation to avoid circular imports
    users: Optional[List["UserBasic"]] = Field(default=[])
    
    class Config:
        orm_mode = True
        from_attributes = True

# Import at the end to avoid circular import issues
from app.schemas.user import UserBasic

# Update forward refs
RoleWithUsers.model_rebuild() 