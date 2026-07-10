from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis, rate_limit_auth
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserRead,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    service = AuthService(session, redis)
    return await service.register(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        organization_name=data.organization_name,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    service = AuthService(session, redis)
    return await service.login(email=data.email, password=data.password)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    service = AuthService(session, redis)
    return await service.refresh(refresh_token=data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: LogoutRequest,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    service = AuthService(session, redis)
    await service.logout(refresh_token=data.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def forgot_password(
    data: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ForgotPasswordResponse:
    service = AuthService(session, redis)
    return await service.forgot_password(email=data.email)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def reset_password(
    data: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    service = AuthService(session, redis)
    await service.reset_password(token=data.token, new_password=data.new_password)
    return MessageResponse(message="Password reset successfully")


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
