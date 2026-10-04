"""
OpportunityOS — User Authentication Service
"""

import hashlib
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.models import UserModel


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class AuthService:
    @staticmethod
    async def get_or_create_demo_user(db: AsyncSession) -> UserModel:
        email = "alex.morgan.dev@gmail.com"
        stmt = select(UserModel).where(UserModel.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            return user

        user = UserModel(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hash_password("password123"),
            full_name="Alex Morgan",
            is_active=True,
            onboarding_completed=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def register_user(
        db: AsyncSession, email: str, password: str, full_name: str
    ) -> UserModel:
        email_clean = email.strip().lower()
        stmt = select(UserModel).where(UserModel.email == email_clean)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError("An account with this email already exists.")

        user = UserModel(
            id=str(uuid.uuid4()),
            email=email_clean,
            hashed_password=hash_password(password),
            full_name=full_name.strip(),
            is_active=True,
            onboarding_completed=False,  # New user starts with onboarding wizard!
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> Optional[UserModel]:
        email_clean = email.strip().lower()
        stmt = select(UserModel).where(UserModel.email == email_clean)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return None
        if user.hashed_password != hash_password(password):
            return None
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
