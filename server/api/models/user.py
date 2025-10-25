"""User models for authentication."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str


class User(UserBase):
    """User model returned to client (without password)."""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: User


class TokenData(BaseModel):
    """Data stored in JWT token."""
    user_id: int
    email: str
