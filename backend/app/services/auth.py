import secrets
import uuid
from datetime import timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import OrganizationRole
from app.models.org_member import OrgMember
from app.models.organization import Organization
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import AuthResponse, ForgotPasswordResponse, UserRead


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis
        self.users = UserRepository(session)

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
    ) -> AuthResponse:
        existing_user = await self.users.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = await self.users.create(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
        )

        organization = Organization(name=organization_name)
        self.session.add(organization)
        await self.session.flush()

        membership = OrgMember(
            organization_id=organization.id,
            user_id=user.id,
            role=OrganizationRole.OWNER,
        )
        self.session.add(membership)

        await self.session.commit()
        await self.session.refresh(user)

        return await self._issue_auth_response(user)

    async def login(self, *, email: str, password: str) -> AuthResponse:
        user = await self.users.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        return await self._issue_auth_response(user)

    async def refresh(self, *, refresh_token: str) -> AuthResponse:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = self._get_required_string_claim(payload, "sub")
        jti = self._get_required_string_claim(payload, "jti")

        blacklisted = await self.redis.get(f"auth:blacklist:{jti}")
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        refresh_key = f"auth:refresh:{jti}"
        stored_user_id_raw = await self.redis.get(refresh_key)
        stored_user_id = self._redis_value_to_string(stored_user_id_raw)

        if stored_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token session not found",
            )

        await self.redis.set(
            f"auth:blacklist:{jti}",
            "1",
            ex=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        user = await self.users.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return await self._issue_auth_response(user)

    async def logout(self, *, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError:
            return

        if payload.get("type") != "refresh":
            return

        jti = payload.get("jti")
        if not isinstance(jti, str):
            return

        await self.redis.delete(f"auth:refresh:{jti}")
        await self.redis.setex(
            f"auth:blacklist:{jti}",
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "1",
        )

    async def forgot_password(self, *, email: str) -> ForgotPasswordResponse:
        user = await self.users.get_by_email(email)

        message = "If the email exists, password reset instructions were sent."

        if not user:
            return ForgotPasswordResponse(message=message)

        reset_token = secrets.token_urlsafe(32)
        key = f"auth:password-reset:{reset_token}"

        await self.redis.set(
            key,
            str(user.id),
            ex=timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )

        if settings.ENV == "development":
            return ForgotPasswordResponse(message=message, reset_token=reset_token)

        return ForgotPasswordResponse(message=message)

    async def reset_password(self, *, token: str, new_password: str) -> None:
        key = f"auth:password-reset:{token}"
        user_id_raw = await self.redis.get(key)
        user_id = self._redis_value_to_string(user_id_raw)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user = await self.users.get_by_id(uuid.UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user.hashed_password = hash_password(new_password)

        await self.redis.delete(key)
        await self.session.commit()

    async def _issue_auth_response(self, user: User) -> AuthResponse:
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        payload = decode_token(refresh_token)
        jti = self._get_required_string_claim(payload, "jti")

        await self.redis.set(
            f"auth:refresh:{jti}",
            str(user.id),
            ex=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserRead.model_validate(user),
        )

    @staticmethod
    def _get_required_string_claim(payload: dict[str, Any], claim_name: str) -> str:
        claim = payload.get(claim_name)

        if not isinstance(claim, str) or not claim:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return claim

    @staticmethod
    def _redis_value_to_string(value: object) -> str | None:
        if value is None:
            return None

        if isinstance(value, bytes):
            return value.decode("utf-8")

        if isinstance(value, str):
            return value

        return None
