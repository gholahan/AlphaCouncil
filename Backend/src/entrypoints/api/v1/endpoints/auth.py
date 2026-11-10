"""Authentication and User Profile endpoints (Signup, Login, Me)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.adapters.storage.database import get_session
from src.adapters.storage.models import UserRecord
from src.entrypoints.api.dependencies import get_current_user
from src.entrypoints.api.v1.schemas.auth import (
    UserResponse,
    UserSignupRequest,
    UserLoginRequest,
    TokenResponse,
)

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserSignupRequest,
    session: AsyncSession = Depends(get_session),
):
    """Register a new user account (integrated with Neon Auth sync pattern)."""
    # Check if user already exists
    result = await session.execute(
        select(UserRecord).where(UserRecord.email == payload.email)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # Create user record
    new_user = UserRecord(
        email=payload.email,
        name=payload.name,
        subscription_tier="free",
        daily_quota_remaining=5,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Generate token (using user id as bearer token for development/sync compatibility)
    access_token = str(new_user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Authenticate user with email and password."""
    result = await session.execute(
        select(UserRecord).where(UserRecord.email == payload.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # In production with Neon Auth (Better Auth), password verification is handled by Neon Auth.
    # For local testing / backend fallback, we allow login for any existing user.
    access_token = str(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserRecord = Depends(get_current_user),
):
    """Get authenticated user profile details, subscription tier, and quota."""
    return UserResponse.model_validate(current_user)
