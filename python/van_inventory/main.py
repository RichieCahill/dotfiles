"""FastAPI app for van inventory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated

import typer
import uvicorn
from fastapi import FastAPI

from python.common import configure_logger
from python.orm.common import get_postgres_engine
from python.van_inventory.routers import api_router, frontend_router

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = get_postgres_engine(name="VAN_INVENTORY")
        yield
        app.state.engine.dispose()

    app = FastAPI(title="Van Inventory", lifespan=lifespan)
    app.include_router(api_router)
    app.include_router(frontend_router)
    return app


def serve(
    # Intentionally binds all interfaces — this is a LAN-only van server
    host: Annotated[str, typer.Option("--host", "-h", help="Host to bind to")] = "0.0.0.0",  # noqa: S104
    port: Annotated[int, typer.Option("--port", "-p", help="Port to bind to")] = 8001,
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Log level")] = "INFO",
) -> None:
    """Start the Van Inventory server."""
    configure_logger(log_level)
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    typer.run(serve)
