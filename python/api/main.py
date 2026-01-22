"""FastAPI interface for Contact database."""

import logging
import shutil
import subprocess
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from fastapi import FastAPI

from python.api.routers import contact_router, create_frontend_router
from python.common import configure_logger
from python.orm.base import get_postgres_engine

logger = logging.getLogger(__name__)


def create_app(frontend_dir: Path | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Manage application lifespan."""
        app.state.engine = get_postgres_engine()
        yield
        app.state.engine.dispose()

    app = FastAPI(title="Contact Database API", lifespan=lifespan)

    app.include_router(contact_router)

    if frontend_dir:
        logger.info(f"Serving frontend from {frontend_dir}")
        frontend_router = create_frontend_router(frontend_dir)
        app.include_router(frontend_router)

    return app


def build_frontend(source_dir: Path | None, cache_dir: Path | None = None) -> Path | None:
    """Run npm build and copy output to a temp directory.

    Works even if source_dir is read-only by copying to a temp directory first.

    Args:
        source_dir: Frontend source directory.
        cache_dir: Optional npm cache directory for faster repeated builds.

    Returns:
        Path to frontend build directory, or None if no source_dir provided.
    """
    if not source_dir:
        return None

    if not source_dir.exists():
        error = f"Frontend directory {source_dir} does not exist"
        raise FileExistsError(error)

    logger.info("Building frontend from %s...", source_dir)

    # Copy source to a writable temp directory
    build_dir = Path(tempfile.mkdtemp(prefix="contact_frontend_build_"))
    shutil.copytree(source_dir, build_dir, dirs_exist_ok=True)

    env = dict(environ)
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        env["npm_config_cache"] = str(cache_dir)

    subprocess.run(["npm", "install"], cwd=build_dir, env=env, check=True)
    subprocess.run(["npm", "run", "build"], cwd=build_dir, env=env, check=True)

    dist_dir = build_dir / "dist"
    if not dist_dir.exists():
        error = f"Build output not found at {dist_dir}"
        raise FileNotFoundError(error)

    output_dir = Path(tempfile.mkdtemp(prefix="contact_frontend_"))
    shutil.copytree(dist_dir, output_dir, dirs_exist_ok=True)
    logger.info(f"Frontend built and copied to {output_dir}")

    shutil.rmtree(build_dir)

    return output_dir


def serve(
    host: Annotated[str, typer.Option("--host", "-h", help="Host to bind to")],
    frontend_dir: Annotated[
        Path | None,
        typer.Option(
            "--frontend-dir",
            "-f",
            help="Frontend source directory. If provided, runs npm build and serves from temp dir.",
        ),
    ] = None,
    port: Annotated[int, typer.Option("--port", "-p", help="Port to bind to")] = 8000,
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Log level")] = "INFO",
) -> None:
    """Start the Contact API server."""
    configure_logger(log_level)

    cache_dir = Path(environ["HOME"]) / ".npm"
    serve_dir = build_frontend(frontend_dir, cache_dir=cache_dir)

    app = create_app(frontend_dir=serve_dir)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    typer.run(serve)
