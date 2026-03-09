"""Extended tests for python/installer/tui.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from python.installer.tui import (
    Cursor,
    State,
    bash_wrapper,
    calculate_device_menu_padding,
    get_device,
    get_devices,
    status_bar,
)


def test_get_devices() -> None:
    """Test get_devices parses lsblk output."""
    mock_output = (
        'NAME="/dev/sda" SIZE="100G" TYPE="disk" MOUNTPOINTS=""\n'
        'NAME="/dev/sda1" SIZE="512M" TYPE="part" MOUNTPOINTS="/boot"\n'
    )
    with patch("python.installer.tui.bash_wrapper", return_value=mock_output):
        devices = get_devices()
    assert len(devices) == 2
    assert devices[0]["name"] == "/dev/sda"
    assert devices[1]["name"] == "/dev/sda1"


def test_calculate_device_menu_padding_with_padding() -> None:
    """Test calculate_device_menu_padding with custom padding."""
    devices = [
        {"name": "abc", "size": "100G"},
        {"name": "abcdef", "size": "500G"},
    ]
    result = calculate_device_menu_padding(devices, "name", 5)
    assert result == len("abcdef") + 5


def test_calculate_device_menu_padding_zero() -> None:
    """Test calculate_device_menu_padding with zero padding."""
    devices = [{"name": "abc"}]
    result = calculate_device_menu_padding(devices, "name", 0)
    assert result == 3


def test_status_bar() -> None:
    """Test status_bar renders without error."""
    import curses as _curses

    mock_screen = MagicMock()
    cursor = Cursor()
    cursor.set_height(50)
    cursor.set_width(100)
    cursor.set_x(5)
    cursor.set_y(10)
    with patch.object(_curses, "color_pair", return_value=0), patch.object(_curses, "A_REVERSE", 0):
        status_bar(mock_screen, cursor, 100, 50)
    assert mock_screen.addstr.call_count > 0


def test_get_device_various_formats() -> None:
    """Test get_device with different formats."""
    raw = 'NAME="/dev/nvme0n1p1" SIZE="1T" TYPE="nvme" MOUNTPOINTS="/"'
    device = get_device(raw)
    assert device["name"] == "/dev/nvme0n1p1"
    assert device["size"] == "1T"
    assert device["type"] == "nvme"
    assert device["mountpoints"] == "/"
