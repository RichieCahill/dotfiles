"""FastAPI interface for Contact database."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import typer
import uvicorn
from fastapi import FastAPI

from python.api.middleware import ZstdMiddleware
from python.api.routers import contact_router, views_router
from python.common import configure_logger
from python.orm.common import get_postgres_engine

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Manage application lifespan."""
        app.state.engine = get_postgres_engine()
        yield
        app.state.engine.dispose()

    app = FastAPI(title="Contact Database API", lifespan=lifespan)
    app.add_middleware(ZstdMiddleware)

    app.include_router(contact_router)
    app.include_router(views_router)

    return app


def serve(
    host: Annotated[str, typer.Option("--host", "-h", help="Host to bind to")],
    port: Annotated[int, typer.Option("--port", "-p", help="Port to bind to")] = 8000,
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Log level")] = "INFO",
) -> None:
    """Start the Contact API server."""
    configure_logger(log_level)

    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    typer.run(serve)
