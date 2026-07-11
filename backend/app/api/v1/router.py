from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.boards import router as boards_router
from app.api.v1.routes.columns import router as columns_router
from app.api.v1.routes.invitations import router as invitations_router
from app.api.v1.routes.organizations import router as organizations_router
from app.api.v1.routes.projects import router as projects_router

api_router = APIRouter()


@api_router.get("/ping", tags=["system"])
async def ping() -> dict[str, str]:
    return {"message": "pong"}


api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(projects_router)
api_router.include_router(boards_router)
api_router.include_router(columns_router)
api_router.include_router(invitations_router)
