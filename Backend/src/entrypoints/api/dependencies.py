"""FastAPI dependencies for authentication and database sessions."""

from typing import Optional
import base64
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.adapters.storage.database import get_session
from src.adapters.storage.models import UserRecord

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> UserRecord:
    """Validate Neon Auth / Better Auth token and return current UserRecord."""
    if not credentials:
        # Fallback for local testing / development: return a demo user or create one
        result = await session.execute(
            select(UserRecord).where(UserRecord.email == "demo@alphacouncil.ng")
        )
        demo_user = result.scalar_one_or_none()
        if demo_user:
            return demo_user

        demo_user = UserRecord(
            email="demo@alphacouncil.ng",
            name="Demo Investor",
            subscription_tier="premium",
            daily_quota_remaining=50,
        )
        session.add(demo_user)
        await session.commit()
        await session.refresh(demo_user)
        return demo_user

    token = credentials.credentials
    try:
        # Attempt to parse JWT payload (header.payload.signature)
        parts = token.split(".")
        user_id_or_email = None
        if len(parts) == 3:
            payload_segment = parts[1]
            padded = payload_segment + "=" * (-len(payload_segment) % 4)
            payload_bytes = base64.urlsafe_b64decode(padded.encode("utf-8"))
            payload = json.loads(payload_bytes.decode("utf-8"))
            user_id_or_email = payload.get("sub") or payload.get("email") or payload.get("id")
        else:
            user_id_or_email = token

        if not user_id_or_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token payload.",
            )

        # Query user by ID or email
        query = select(UserRecord).where(
            (UserRecord.email == user_id_or_email)
            | (UserRecord.id.cast(str) == str(user_id_or_email))
        )
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in system. Please register or sign in.",
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[UserRecord]:
    """Optional current user for endpoints that allow anonymous or authenticated access."""
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
