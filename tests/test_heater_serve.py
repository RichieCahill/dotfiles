"""Tests for heater/main.py serve function and lifespan."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from click.exceptions import Exit

from python.heater.models import DeviceConfig


def test_serve_missing_params() -> None:
    """Test serve raises when device params are missing."""
    mock_tinytuya = MagicMock()
    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import serve

        with pytest.raises(Exit):
            serve(host="localhost", port=8124, log_level="INFO")


def test_serve_with_params() -> None:
    """Test serve starts uvicorn when params provided."""
    mock_tinytuya = MagicMock()
    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import serve

        with patch("python.heater.main.uvicorn.run") as mock_run:
            serve(
                host="localhost",
                port=8124,
                log_level="INFO",
                device_id="abc",
                device_ip="10.0.0.1",
                local_key="key123",
            )
            mock_run.assert_called_once()


def test_heater_off_route_failure() -> None:
    """Test /off route raises HTTPException on failure."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.set_value.side_effect = ConnectionError("fail")
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app
        from python.heater.controller import HeaterController
        from fastapi import HTTPException

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)
        app.state.controller = HeaterController(config)

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/off":
                with pytest.raises(HTTPException):
                    route.endpoint()
                break


def test_heater_toggle_route_failure() -> None:
    """Test /toggle route raises HTTPException on failure."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    # toggle calls status() first then set_value - make set_value fail
    mock_device.status.return_value = {"dps": {"1": True}}
    mock_device.set_value.side_effect = ConnectionError("fail")
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app
        from python.heater.controller import HeaterController
        from fastapi import HTTPException

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)
        app.state.controller = HeaterController(config)

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/toggle":
                with pytest.raises(HTTPException):
                    route.endpoint()
                break
