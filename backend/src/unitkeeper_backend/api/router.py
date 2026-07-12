from __future__ import annotations

from fastapi import APIRouter

from unitkeeper_backend.api.routers.auth import router as auth_router
from unitkeeper_backend.api.routers.balances import router as balances_router
from unitkeeper_backend.api.routers.groups import router as groups_router
from unitkeeper_backend.api.routers.health import router as health_router
from unitkeeper_backend.api.routers.internal_bot import router as internal_bot_router
from unitkeeper_backend.api.routers.sprints import router as sprints_router
from unitkeeper_backend.api.routers.tasks import router as tasks_router


def build_api_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(health_router)
    router.include_router(auth_router)
    router.include_router(balances_router)
    router.include_router(groups_router)
    router.include_router(tasks_router)
    router.include_router(sprints_router)
    router.include_router(internal_bot_router)
    return router
