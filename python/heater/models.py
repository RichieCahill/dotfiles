"""Pydantic models for heater API."""

from pydantic import BaseModel, Field


class DeviceConfig(BaseModel):
    """Tuya device configuration."""

    device_id: str
    ip: str
    local_key: str
    version: float = 3.5


class HeaterStatus(BaseModel):
    """Current heater status."""

    power: bool
    setpoint: int | None = None
    state: str | None = None  # "Stop", "Heat", etc.
    error_code: int | None = None
    raw_dps: dict[str, object] = Field(default_factory=dict)


class ActionResult(BaseModel):
    """Result of a heater action."""

    success: bool
    action: str
    power: bool | None = None
    error: str | None = None
