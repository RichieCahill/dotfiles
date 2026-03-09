"""Extended tests for python/installer modules."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from python.installer.__main__ import (
    bash_wrapper,
    create_zfs_pool,
    get_cpu_manufacturer,
    partition_disk,
)
from python.installer.tui import (
    Cursor,
    State,
    bash_wrapper as tui_bash_wrapper,
    get_device,
    calculate_device_menu_padding,
)


# --- installer __main__ tests ---


def test_installer_bash_wrapper_success() -> None:
    """Test installer bash_wrapper on success."""
    result = bash_wrapper("echo hello")
    assert result.strip() == "hello"


def test_installer_bash_wrapper_error() -> None:
    """Test installer bash_wrapper raises on error."""
    with pytest.raises(RuntimeError, match="Failed to run command"):
        bash_wrapper("ls /nonexistent/path/that/does/not/exist")


def test_partition_disk() -> None:
    """Test partition_disk calls commands correctly."""
    with patch("python.installer.__main__.bash_wrapper") as mock_bash:
        partition_disk("/dev/sda", swap_size=8, reserve=0)
    assert mock_bash.call_count == 2


def test_partition_disk_with_reserve() -> None:
    """Test partition_disk with reserve space."""
    with patch("python.installer.__main__.bash_wrapper") as mock_bash:
        partition_disk("/dev/sda", swap_size=8, reserve=10)
    assert mock_bash.call_count == 2


def test_partition_disk_minimum_swap() -> None:
    """Test partition_disk enforces minimum swap size."""
    with patch("python.installer.__main__.bash_wrapper") as mock_bash:
        partition_disk("/dev/sda", swap_size=0, reserve=-1)
    # swap_size should be clamped to 1, reserve to 0
    assert mock_bash.call_count == 2


def test_create_zfs_pool_single_disk() -> None:
    """Test create_zfs_pool with single disk."""
    with patch("python.installer.__main__.bash_wrapper") as mock_bash:
        mock_bash.return_value = "NAME\nroot_pool\n"
        create_zfs_pool(["/dev/sda-part2"], "/mnt")
    assert mock_bash.call_count == 2


def test_create_zfs_pool_mirror() -> None:
    """Test create_zfs_pool with mirror disks."""
    with patch("python.installer.__main__.bash_wrapper") as mock_bash:
        mock_bash.return_value = "NAME\nroot_pool\n"
        create_zfs_pool(["/dev/sda-part2", "/dev/sdb-part2"], "/mnt")
    assert mock_bash.call_count == 2


def test_create_zfs_pool_no_disks() -> None:
    """Test create_zfs_pool raises with no disks."""
    with pytest.raises(ValueError, match="disks must be a tuple"):
        create_zfs_pool([], "/mnt")


def test_get_cpu_manufacturer_amd() -> None:
    """Test get_cpu_manufacturer with AMD CPU."""
    output = "vendor_id\t: AuthenticAMD\nmodel name\t: AMD Ryzen 9\n"
    with patch("python.installer.__main__.bash_wrapper", return_value=output):
        assert get_cpu_manufacturer() == "amd"


def test_get_cpu_manufacturer_intel() -> None:
    """Test get_cpu_manufacturer with Intel CPU."""
    output = "vendor_id\t: GenuineIntel\nmodel name\t: Intel Core i9\n"
    with patch("python.installer.__main__.bash_wrapper", return_value=output):
        assert get_cpu_manufacturer() == "intel"


def test_get_cpu_manufacturer_unknown() -> None:
    """Test get_cpu_manufacturer with unknown CPU raises."""
    output = "model name\t: Unknown CPU\n"
    with (
        patch("python.installer.__main__.bash_wrapper", return_value=output),
        pytest.raises(RuntimeError, match="Failed to get CPU manufacturer"),
    ):
        get_cpu_manufacturer()


# --- tui bash_wrapper tests ---


def test_tui_bash_wrapper_success() -> None:
    """Test tui bash_wrapper success."""
    result = tui_bash_wrapper("echo hello")
    assert result.strip() == "hello"


def test_tui_bash_wrapper_error() -> None:
    """Test tui bash_wrapper raises on error."""
    with pytest.raises(RuntimeError, match="Failed to run command"):
        tui_bash_wrapper("ls /nonexistent/path/that/does/not/exist")


# --- Cursor boundary tests ---


def test_cursor_move_at_boundaries() -> None:
    """Test cursor doesn't go below 0."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_x(0)
    c.set_y(0)
    c.move_up()
    assert c.get_y() == 0
    c.move_left()
    assert c.get_x() == 0


def test_cursor_move_at_max_boundaries() -> None:
    """Test cursor doesn't exceed max."""
    c = Cursor()
    c.set_height(5)
    c.set_width(10)
    c.set_x(9)
    c.set_y(4)
    c.move_down()
    assert c.get_y() == 4
    c.move_right()
    assert c.get_x() == 9


# --- get_device additional ---


def test_get_device_with_mountpoint() -> None:
    """Test get_device with mountpoint."""
    raw = 'NAME="/dev/sda1" SIZE="512M" TYPE="part" MOUNTPOINTS="/boot"'
    device = get_device(raw)
    assert device["mountpoints"] == "/boot"


# --- State additional ---


def test_state_selected_devices_empty() -> None:
    """Test State get_selected_devices when empty."""
    s = State()
    result = s.get_selected_devices()
    assert result == ()
