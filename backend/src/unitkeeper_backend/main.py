from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from unitkeeper_backend.api.router import build_api_router
from unitkeeper_backend.config import settings
from unitkeeper_backend.di import setup_di
from unitkeeper_backend.domain.errors import DomainError


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.include_router(build_api_router())
    app.add_exception_handler(DomainError, domain_error_handler)
    setup_di(app)
    return app


async def domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    payload: dict[str, object] = {"code": exc.code, "message": exc.message}
    if exc.details is not None:
        payload["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=payload)


app = create_app()
