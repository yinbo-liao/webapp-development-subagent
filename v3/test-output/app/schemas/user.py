from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base schema for User"""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    full_name: Optional[str]

class UserCreate(UserBase):
    """Schema for creating User"""
    pass

class UserUpdate(UserBase):
    """Schema for updating User"""
    pass

class UserInDB(UserBase):
    """Schema for User as stored in database"""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

class UserResponse(UserInDB):
    """Schema for API response - excludes sensitive fields"""
    pass
