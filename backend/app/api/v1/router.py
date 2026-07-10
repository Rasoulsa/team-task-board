from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router

api_router = APIRouter()


@api_router.get("/ping", tags=["system"])
async def ping() -> dict[str, str]:
    return {"message": "pong"}


api_router.include_router(auth_router)
