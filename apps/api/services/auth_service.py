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
        # 1. If an actual registered user exists, return the latest registered user
        stmt = (
            select(UserModel)
            .where(~UserModel.email.ilike("%alex.morgan%"))
            .order_by(UserModel.created_at.desc())
        )
        res = await db.execute(stmt)
        user = res.scalars().first()
        if user:
            return user

        # 2. Check for existing generic demo user
        demo_email = "engineer@opportunityos.internal"
        stmt_demo = select(UserModel).where(UserModel.email == demo_email)
        res_demo = await db.execute(stmt_demo)
        demo_user = res_demo.scalar_one_or_none()
        if demo_user:
            return demo_user

        # 3. Create generic demo user
        user = UserModel(
            id=str(uuid.uuid4()),
            email=demo_email,
            hashed_password=hash_password("password123"),
            full_name="Lead Engineer",
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
