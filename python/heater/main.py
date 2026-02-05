"""FastAPI heater control service."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import typer
import uvicorn
from fastapi import FastAPI, HTTPException

from python.common import configure_logger
from python.heater.controller import HeaterController
from python.heater.models import ActionResult, DeviceConfig, HeaterStatus

logger = logging.getLogger(__name__)


def create_app(config: DeviceConfig) -> FastAPI:
    """Create FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.controller = HeaterController(config)
        yield

    app = FastAPI(
        title="Heater Control API",
        description="Fast local control for Tuya heater",
        lifespan=lifespan,
    )

    @app.get("/status")
    def get_status() -> HeaterStatus:
        return app.state.controller.status()

    @app.post("/on")
    def heater_on() -> ActionResult:
        result = app.state.controller.turn_on()
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        return result

    @app.post("/off")
    def heater_off() -> ActionResult:
        result = app.state.controller.turn_off()
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        return result

    @app.post("/toggle")
    def heater_toggle() -> ActionResult:
        result = app.state.controller.toggle()
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        return result

    return app


def serve(
    host: Annotated[str, typer.Option("--host", "-h", help="Host to bind to")],
    port: Annotated[int, typer.Option("--port", "-p", help="Port to bind to")] = 8124,
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Log level")] = "INFO",
    device_id: Annotated[str | None, typer.Option("--device-id", envvar="TUYA_DEVICE_ID")] = None,
    device_ip: Annotated[str | None, typer.Option("--device-ip", envvar="TUYA_DEVICE_IP")] = None,
    local_key: Annotated[str | None, typer.Option("--local-key", envvar="TUYA_LOCAL_KEY")] = None,
) -> None:
    """Start the heater control API server."""
    configure_logger(log_level)

    logger.info("Starting heater control API server")

    if not device_id or not device_ip or not local_key:
        error = "Must provide device ID, IP, and local key"
        raise typer.Exit(error)

    config = DeviceConfig(device_id=device_id, ip=device_ip, local_key=local_key)

    app = create_app(config)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    typer.run(serve)
