from fastapi import APIRouter

from app.api.v1.routes import (
    activity,
    auth,
    boards,
    cards,
    columns,
    comments,
    invitations,
    notifications,
    organizations,
    ping,
    projects,
    stats,
)

api_router = APIRouter()

api_router.include_router(ping.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(projects.router)
api_router.include_router(boards.router)
api_router.include_router(columns.router)
api_router.include_router(cards.router)
api_router.include_router(comments.router)
api_router.include_router(invitations.router)
api_router.include_router(stats.router)
api_router.include_router(activity.router)
api_router.include_router(notifications.router)
