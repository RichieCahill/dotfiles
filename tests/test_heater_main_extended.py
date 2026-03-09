"""Extended tests for python/heater/main.py - FastAPI routes."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from python.heater.models import ActionResult, DeviceConfig, HeaterStatus


def test_heater_app_routes() -> None:
    """Test heater app has expected routes."""
    mock_tinytuya = MagicMock()
    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)

    route_paths = [r.path for r in app.routes]
    assert "/status" in route_paths
    assert "/on" in route_paths
    assert "/off" in route_paths
    assert "/toggle" in route_paths


def test_heater_get_status_route() -> None:
    """Test /status route handler."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.status.return_value = {"dps": {"1": True, "101": 72}}
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)

        # Simulate lifespan by setting controller
        app.state.controller = HeaterController(config)

        # Find and call the status handler
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/status":
                result = route.endpoint()
                assert result.power is True
                break


def test_heater_on_route() -> None:
    """Test /on route handler."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.set_value.return_value = None
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)
        app.state.controller = HeaterController(config)

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/on":
                result = route.endpoint()
                assert result.success is True
                break


def test_heater_off_route() -> None:
    """Test /off route handler."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.set_value.return_value = None
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)
        app.state.controller = HeaterController(config)

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/off":
                result = route.endpoint()
                assert result.success is True
                break


def test_heater_toggle_route() -> None:
    """Test /toggle route handler."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.status.return_value = {"dps": {"1": True}}
    mock_device.set_value.return_value = None
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)
        app.state.controller = HeaterController(config)

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/toggle":
                result = route.endpoint()
                assert result.success is True
                break


def test_heater_on_route_failure() -> None:
    """Test /on route raises HTTPException on failure."""
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

        import pytest

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/on":
                with pytest.raises(HTTPException):
                    route.endpoint()
                break
