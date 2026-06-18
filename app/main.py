from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes import health, jobs
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.startup import validate_startup_configuration


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    validate_startup_configuration()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(jobs.router)
    return app


app = create_app()
