"""Tests for python/installer modules."""

from __future__ import annotations

import curses
from unittest.mock import MagicMock, patch

import pytest

from python.installer.tui import (
    Cursor,
    State,
    calculate_device_menu_padding,
    get_device,
)


# --- Cursor tests ---


def test_cursor_init() -> None:
    """Test Cursor initialization."""
    c = Cursor()
    assert c.get_x() == 0
    assert c.get_y() == 0
    assert c.height == 0
    assert c.width == 0


def test_cursor_set_height_width() -> None:
    """Test Cursor set_height and set_width."""
    c = Cursor()
    c.set_height(100)
    c.set_width(200)
    assert c.height == 100
    assert c.width == 200


def test_cursor_bounce_check() -> None:
    """Test Cursor bounce checks."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)

    assert c.x_bounce_check(-1) == 0
    assert c.x_bounce_check(25) == 19
    assert c.x_bounce_check(5) == 5

    assert c.y_bounce_check(-1) == 0
    assert c.y_bounce_check(15) == 9
    assert c.y_bounce_check(5) == 5


def test_cursor_set_x_y() -> None:
    """Test Cursor set_x and set_y."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_x(5)
    c.set_y(3)
    assert c.get_x() == 5
    assert c.get_y() == 3


def test_cursor_set_x_y_bounds() -> None:
    """Test Cursor set_x and set_y with bounds."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_x(-5)
    assert c.get_x() == 0
    c.set_y(100)
    assert c.get_y() == 9


def test_cursor_move_up() -> None:
    """Test Cursor move_up."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_y(5)
    c.move_up()
    assert c.get_y() == 4


def test_cursor_move_down() -> None:
    """Test Cursor move_down."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_y(5)
    c.move_down()
    assert c.get_y() == 6


def test_cursor_move_left() -> None:
    """Test Cursor move_left."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_x(5)
    c.move_left()
    assert c.get_x() == 4


def test_cursor_move_right() -> None:
    """Test Cursor move_right."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_x(5)
    c.move_right()
    assert c.get_x() == 6


def test_cursor_navigation() -> None:
    """Test Cursor navigation with arrow keys."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_x(5)
    c.set_y(5)

    c.navigation(curses.KEY_UP)
    assert c.get_y() == 4
    c.navigation(curses.KEY_DOWN)
    assert c.get_y() == 5
    c.navigation(curses.KEY_LEFT)
    assert c.get_x() == 4
    c.navigation(curses.KEY_RIGHT)
    assert c.get_x() == 5


def test_cursor_navigation_unknown_key() -> None:
    """Test Cursor navigation with unknown key (no-op)."""
    c = Cursor()
    c.set_height(10)
    c.set_width(20)
    c.set_x(5)
    c.set_y(5)
    c.navigation(999)  # Unknown key
    assert c.get_x() == 5
    assert c.get_y() == 5


# --- State tests ---


def test_state_init() -> None:
    """Test State initialization."""
    s = State()
    assert s.key == 0
    assert s.swap_size == 0
    assert s.reserve_size == 0
    assert s.selected_device_ids == set()
    assert s.show_swap_input is False
    assert s.show_reserve_input is False


def test_state_get_selected_devices() -> None:
    """Test State.get_selected_devices."""
    s = State()
    s.selected_device_ids = {"/dev/sda", "/dev/sdb"}
    result = s.get_selected_devices()
    assert isinstance(result, tuple)
    assert set(result) == {"/dev/sda", "/dev/sdb"}


# --- get_device tests ---


def test_get_device() -> None:
    """Test get_device parses device string."""
    raw = 'NAME="/dev/sda" SIZE="100G" TYPE="disk" MOUNTPOINTS=""'
    device = get_device(raw)
    assert device["name"] == "/dev/sda"
    assert device["size"] == "100G"
    assert device["type"] == "disk"


# --- calculate_device_menu_padding ---


def test_calculate_device_menu_padding() -> None:
    """Test calculate_device_menu_padding."""
    devices = [
        {"name": "/dev/sda", "size": "100G"},
        {"name": "/dev/nvme0n1", "size": "500G"},
    ]
    padding = calculate_device_menu_padding(devices, "name", 2)
    assert padding == len("/dev/nvme0n1") + 2
