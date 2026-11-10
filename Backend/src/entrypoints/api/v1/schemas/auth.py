"""Authentication & User API Schemas."""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    """User profile response schema."""

    id: UUID
    email: str
    name: str
    subscription_tier: str
    daily_quota_remaining: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserSignupRequest(BaseModel):
    """User signup request schema."""

    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    password: Optional[str] = Field(None, description="Optional password for local auth")


class UserLoginRequest(BaseModel):
    """User login request schema."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
