"""Tests for python/heater modules."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from python.heater.models import ActionResult, DeviceConfig, HeaterStatus

if TYPE_CHECKING:
    pass


# --- models tests ---


def test_device_config() -> None:
    """Test DeviceConfig creation."""
    config = DeviceConfig(device_id="abc123", ip="192.168.1.1", local_key="key123")
    assert config.device_id == "abc123"
    assert config.ip == "192.168.1.1"
    assert config.local_key == "key123"
    assert config.version == 3.5


def test_device_config_custom_version() -> None:
    """Test DeviceConfig with custom version."""
    config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key", version=3.3)
    assert config.version == 3.3


def test_heater_status_defaults() -> None:
    """Test HeaterStatus default values."""
    status = HeaterStatus(power=True)
    assert status.power is True
    assert status.setpoint is None
    assert status.state is None
    assert status.error_code is None
    assert status.raw_dps == {}


def test_heater_status_full() -> None:
    """Test HeaterStatus with all fields."""
    status = HeaterStatus(
        power=True,
        setpoint=72,
        state="Heat",
        error_code=0,
        raw_dps={"1": True, "101": 72},
    )
    assert status.power is True
    assert status.setpoint == 72
    assert status.state == "Heat"


def test_action_result_success() -> None:
    """Test ActionResult success."""
    result = ActionResult(success=True, action="on", power=True)
    assert result.success is True
    assert result.action == "on"
    assert result.power is True
    assert result.error is None


def test_action_result_failure() -> None:
    """Test ActionResult failure."""
    result = ActionResult(success=False, action="on", error="Connection failed")
    assert result.success is False
    assert result.error == "Connection failed"


# --- controller tests (with mocked tinytuya) ---


def _get_controller_class() -> type:
    """Import HeaterController with mocked tinytuya."""
    mock_tinytuya = MagicMock()
    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        # Force reimport
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        return HeaterController


def test_heater_controller_status_success() -> None:
    """Test HeaterController.status returns correct status."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.status.return_value = {"dps": {"1": True, "101": 72, "102": "Heat", "108": 0}}
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        status = controller.status()

    assert status.power is True
    assert status.setpoint == 72
    assert status.state == "Heat"


def test_heater_controller_status_error() -> None:
    """Test HeaterController.status handles device error."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.status.return_value = {"Error": "Connection timeout"}
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        status = controller.status()

    assert status.power is False


def test_heater_controller_turn_on() -> None:
    """Test HeaterController.turn_on."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.set_value.return_value = None
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        result = controller.turn_on()

    assert result.success is True
    assert result.action == "on"
    assert result.power is True


def test_heater_controller_turn_on_error() -> None:
    """Test HeaterController.turn_on handles errors."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.set_value.side_effect = ConnectionError("timeout")
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        result = controller.turn_on()

    assert result.success is False
    assert "timeout" in result.error


def test_heater_controller_turn_off() -> None:
    """Test HeaterController.turn_off."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.set_value.return_value = None
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        result = controller.turn_off()

    assert result.success is True
    assert result.action == "off"
    assert result.power is False


def test_heater_controller_turn_off_error() -> None:
    """Test HeaterController.turn_off handles errors."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.set_value.side_effect = ConnectionError("timeout")
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        result = controller.turn_off()

    assert result.success is False


def test_heater_controller_toggle_on_to_off() -> None:
    """Test HeaterController.toggle when heater is on."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.status.return_value = {"dps": {"1": True}}
    mock_device.set_value.return_value = None
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        result = controller.toggle()

    assert result.success is True
    assert result.action == "off"


def test_heater_controller_toggle_off_to_on() -> None:
    """Test HeaterController.toggle when heater is off."""
    mock_tinytuya = MagicMock()
    mock_device = MagicMock()
    mock_device.status.return_value = {"dps": {"1": False}}
    mock_device.set_value.return_value = None
    mock_tinytuya.Device.return_value = mock_device

    with patch.dict(sys.modules, {"tinytuya": mock_tinytuya}):
        if "python.heater.controller" in sys.modules:
            del sys.modules["python.heater.controller"]
        from python.heater.controller import HeaterController

        config = DeviceConfig(device_id="abc", ip="10.0.0.1", local_key="key")
        controller = HeaterController(config)
        result = controller.toggle()

    assert result.success is True
    assert result.action == "on"
