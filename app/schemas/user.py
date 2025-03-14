"""
User schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional, List, ForwardRef

from pydantic import BaseModel, EmailStr, Field, validator


# Create a basic user schema for role relationships to avoid circular imports
class UserBasic(BaseModel):
    """Basic user info for role relationships."""
    id: int
    username: str
    firstname: str
    lastname: str
    
    class Config:
        orm_mode = True
        from_attributes = True


class UserBase(BaseModel):
    """Base schema for user data."""
    username: str
    firstname: str
    lastname: str
    email: Optional[EmailStr] = None
    costcenter: Optional[str] = None
    ba: Optional[str] = None
    part: Optional[str] = None
    area: Optional[str] = None
    job_name: Optional[str] = None
    level: Optional[str] = None
    div_name: Optional[str] = None
    dep_name: Optional[str] = None
    org_name: Optional[str] = None
    position: Optional[str] = None
    role: str = "user"  # Legacy field, kept for backward compatibility
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)
    role_ids: Optional[List[int]] = None  # IDs of roles to assign

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    costcenter: Optional[str] = None
    ba: Optional[str] = None
    part: Optional[str] = None
    area: Optional[str] = None
    job_name: Optional[str] = None
    level: Optional[str] = None
    div_name: Optional[str] = None
    dep_name: Optional[str] = None
    org_name: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None  # Legacy field
    role_ids: Optional[List[int]] = None  # IDs of roles to assign/update
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    """Schema for user in database."""
    id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class User(UserInDBBase):
    """Schema for user response (without sensitive data)."""
    # Use string annotation to avoid circular imports
    roles: Optional[List["Role"]] = Field(default=[])


class UserInDB(UserInDBBase):
    """Schema for user in database (with password hash)."""
    password_hash: str

# Import at the end to avoid circular import issues
from app.schemas.role import Role

# Update forward refs
User.model_rebuild() 