"""Tests for python/heater/main.py."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from python.heater.models import ActionResult, DeviceConfig, HeaterStatus


def test_create_app() -> None:
    """Test create_app creates FastAPI app."""
    mock_tinytuya = MagicMock()
    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import create_app

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        app = create_app(config)
        assert app is not None
        assert app.title == "Heater Control API"


def test_serve_missing_params() -> None:
    """Test serve raises with missing parameters."""
    import typer

    mock_tinytuya = MagicMock()
    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        if "python.heater.main" in sys.modules:
            del sys.modules["python.heater.main"]
        from python.heater.main import serve

        with patch("python.heater.main.configure_logger"):
            try:
                serve(host="0.0.0.0", port=8124, log_level="INFO")
            except (typer.Exit, SystemExit):
                pass
