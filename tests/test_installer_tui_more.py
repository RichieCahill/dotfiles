"""Additional tests for python/installer/tui.py covering missing lines."""

from __future__ import annotations

import curses
from unittest.mock import MagicMock, call, patch

from python.installer.tui import (
    State,
    debug_menu,
    draw_device_ids,
    draw_device_menu,
    draw_menu,
    get_device_id_mapping,
    get_text_input,
    reserve_size_input,
    set_color,
    swap_size_input,
)


# --- set_color (lines 153-156) ---


def test_set_color() -> None:
    """Test set_color initializes curses colors."""
    with (
        patch("python.installer.tui.curses.start_color") as mock_start,
        patch("python.installer.tui.curses.use_default_colors") as mock_defaults,
        patch("python.installer.tui.curses.init_pair") as mock_init_pair,
        patch.object(curses, "COLORS", 8, create=True),
    ):
        set_color()

    mock_start.assert_called_once()
    mock_defaults.assert_called_once()
    assert mock_init_pair.call_count == 8
    mock_init_pair.assert_any_call(1, 0, -1)
    mock_init_pair.assert_any_call(8, 7, -1)


# --- debug_menu (lines 166-175) ---


def test_debug_menu_with_key_pressed() -> None:
    """Test debug_menu when a key has been pressed."""
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (40, 80)

    with patch("python.installer.tui.curses.color_pair", return_value=0):
        debug_menu(mock_screen, ord("a"))

    # Should show width/height, key pressed, and color blocks
    assert mock_screen.addstr.call_count >= 3


def test_debug_menu_no_key_pressed() -> None:
    """Test debug_menu when no key has been pressed (key=0)."""
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (40, 80)

    with patch("python.installer.tui.curses.color_pair", return_value=0):
        debug_menu(mock_screen, 0)

    # Check that "No key press detected..." is displayed
    calls = [str(c) for c in mock_screen.addstr.call_args_list]
    assert any("No key press detected" in c for c in calls)


# --- get_text_input (lines 190-208) ---


def test_get_text_input_enter_key() -> None:
    """Test get_text_input returns input when Enter is pressed."""
    mock_screen = MagicMock()
    mock_screen.getch.side_effect = [ord("h"), ord("i"), ord("\n")]

    with patch("python.installer.tui.curses.echo"), patch("python.installer.tui.curses.noecho"):
        result = get_text_input(mock_screen, "Prompt: ", 5, 0)

    assert result == "hi"


def test_get_text_input_escape_key() -> None:
    """Test get_text_input returns empty string when Escape is pressed."""
    mock_screen = MagicMock()
    mock_screen.getch.side_effect = [ord("h"), ord("i"), 27]  # 27 = ESC

    with patch("python.installer.tui.curses.echo"), patch("python.installer.tui.curses.noecho"):
        result = get_text_input(mock_screen, "Prompt: ", 5, 0)

    assert result == ""


def test_get_text_input_backspace() -> None:
    """Test get_text_input handles backspace correctly."""
    mock_screen = MagicMock()
    mock_screen.getch.side_effect = [ord("h"), ord("i"), 127, ord("\n")]  # 127 = backspace

    with patch("python.installer.tui.curses.echo"), patch("python.installer.tui.curses.noecho"):
        result = get_text_input(mock_screen, "Prompt: ", 5, 0)

    assert result == "h"


def test_get_text_input_curses_backspace() -> None:
    """Test get_text_input handles curses KEY_BACKSPACE."""
    mock_screen = MagicMock()
    mock_screen.getch.side_effect = [ord("a"), ord("b"), curses.KEY_BACKSPACE, ord("\n")]

    with patch("python.installer.tui.curses.echo"), patch("python.installer.tui.curses.noecho"):
        result = get_text_input(mock_screen, "Prompt: ", 5, 0)

    assert result == "a"


# --- swap_size_input (lines 226-241) ---


def test_swap_size_input_no_trigger() -> None:
    """Test swap_size_input when not triggered (no enter on swap row)."""
    mock_screen = MagicMock()
    state = State()
    state.key = ord("a")

    result = swap_size_input(mock_screen, state, swap_offset=5)

    assert result.swap_size == 0
    assert result.show_swap_input is False


def test_swap_size_input_enter_triggers_input() -> None:
    """Test swap_size_input when Enter is pressed on the swap row."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(20)
    state.cursor.set_width(80)
    state.cursor.set_y(5)
    state.key = ord("\n")

    with patch("python.installer.tui.get_text_input", return_value="16"):
        result = swap_size_input(mock_screen, state, swap_offset=5)

    assert result.swap_size == 16
    assert result.show_swap_input is False


def test_swap_size_input_invalid_value() -> None:
    """Test swap_size_input with invalid (non-integer) input."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(20)
    state.cursor.set_width(80)
    state.cursor.set_y(5)
    state.key = ord("\n")

    with patch("python.installer.tui.get_text_input", return_value="abc"):
        result = swap_size_input(mock_screen, state, swap_offset=5)

    assert result.swap_size == 0
    assert result.show_swap_input is False
    # Should have shown "Invalid input" message and waited for a key
    mock_screen.getch.assert_called_once()


def test_swap_size_input_already_showing() -> None:
    """Test swap_size_input when show_swap_input is already True."""
    mock_screen = MagicMock()
    state = State()
    state.show_swap_input = True
    state.key = 0

    with patch("python.installer.tui.get_text_input", return_value="8"):
        result = swap_size_input(mock_screen, state, swap_offset=5)

    assert result.swap_size == 8
    assert result.show_swap_input is False


# --- reserve_size_input (lines 259-274) ---


def test_reserve_size_input_no_trigger() -> None:
    """Test reserve_size_input when not triggered."""
    mock_screen = MagicMock()
    state = State()
    state.key = ord("a")

    result = reserve_size_input(mock_screen, state, reserve_offset=6)

    assert result.reserve_size == 0
    assert result.show_reserve_input is False


def test_reserve_size_input_enter_triggers_input() -> None:
    """Test reserve_size_input when Enter is pressed on the reserve row."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(20)
    state.cursor.set_width(80)
    state.cursor.set_y(6)
    state.key = ord("\n")

    with patch("python.installer.tui.get_text_input", return_value="32"):
        result = reserve_size_input(mock_screen, state, reserve_offset=6)

    assert result.reserve_size == 32
    assert result.show_reserve_input is False


def test_reserve_size_input_invalid_value() -> None:
    """Test reserve_size_input with invalid (non-integer) input."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(20)
    state.cursor.set_width(80)
    state.cursor.set_y(6)
    state.key = ord("\n")

    with patch("python.installer.tui.get_text_input", return_value="xyz"):
        result = reserve_size_input(mock_screen, state, reserve_offset=6)

    assert result.reserve_size == 0
    assert result.show_reserve_input is False
    mock_screen.getch.assert_called_once()


def test_reserve_size_input_already_showing() -> None:
    """Test reserve_size_input when show_reserve_input is already True."""
    mock_screen = MagicMock()
    state = State()
    state.show_reserve_input = True
    state.key = 0

    with patch("python.installer.tui.get_text_input", return_value="10"):
        result = reserve_size_input(mock_screen, state, reserve_offset=6)

    assert result.reserve_size == 10
    assert result.show_reserve_input is False


# --- get_device_id_mapping (lines 308-316) ---


def test_get_device_id_mapping() -> None:
    """Test get_device_id_mapping returns correct mapping."""
    find_output = "/dev/disk/by-id/ata-DISK1\n/dev/disk/by-id/ata-DISK2\n"

    def mock_bash(cmd: str) -> str:
        if cmd.startswith("find"):
            return find_output
        if "ata-DISK1" in cmd:
            return "/dev/sda\n"
        if "ata-DISK2" in cmd:
            return "/dev/sda\n"
        return ""

    with patch("python.installer.tui.bash_wrapper", side_effect=mock_bash):
        result = get_device_id_mapping()

    assert "/dev/sda" in result
    assert "/dev/disk/by-id/ata-DISK1" in result["/dev/sda"]
    assert "/dev/disk/by-id/ata-DISK2" in result["/dev/sda"]


def test_get_device_id_mapping_multiple_devices() -> None:
    """Test get_device_id_mapping with multiple different devices."""
    find_output = "/dev/disk/by-id/ata-DISK1\n/dev/disk/by-id/nvme-DISK2\n"

    def mock_bash(cmd: str) -> str:
        if cmd.startswith("find"):
            return find_output
        if "ata-DISK1" in cmd:
            return "/dev/sda\n"
        if "nvme-DISK2" in cmd:
            return "/dev/nvme0n1\n"
        return ""

    with patch("python.installer.tui.bash_wrapper", side_effect=mock_bash):
        result = get_device_id_mapping()

    assert "/dev/sda" in result
    assert "/dev/nvme0n1" in result


# --- draw_device_ids (lines 354-372) ---


def test_draw_device_ids_no_selection() -> None:
    """Test draw_device_ids without selecting any device."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(40)
    state.cursor.set_width(80)
    state.key = 0
    device_ids = {"/dev/disk/by-id/ata-DISK1"}
    menu_width = list(range(0, 60))

    with (
        patch("python.installer.tui.curses.A_BOLD", 1),
        patch("python.installer.tui.curses.color_pair", return_value=0),
    ):
        result_state, result_row = draw_device_ids(state, 2, 0, mock_screen, menu_width, device_ids)

    assert result_row == 3
    assert len(result_state.selected_device_ids) == 0


def test_draw_device_ids_select_device() -> None:
    """Test draw_device_ids selecting a device with space key."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(40)
    state.cursor.set_width(80)
    state.cursor.set_y(3)
    state.cursor.set_x(0)
    state.key = ord(" ")
    device_ids = {"/dev/disk/by-id/ata-DISK1"}
    menu_width = list(range(0, 60))

    with (
        patch("python.installer.tui.curses.A_BOLD", 1),
        patch("python.installer.tui.curses.color_pair", return_value=0),
    ):
        result_state, result_row = draw_device_ids(state, 2, 0, mock_screen, menu_width, device_ids)

    assert "/dev/disk/by-id/ata-DISK1" in result_state.selected_device_ids


def test_draw_device_ids_deselect_device() -> None:
    """Test draw_device_ids deselecting an already selected device."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(40)
    state.cursor.set_width(80)
    state.cursor.set_y(3)
    state.cursor.set_x(0)
    state.key = ord(" ")
    state.selected_device_ids.add("/dev/disk/by-id/ata-DISK1")
    device_ids = {"/dev/disk/by-id/ata-DISK1"}
    menu_width = list(range(0, 60))

    with (
        patch("python.installer.tui.curses.A_BOLD", 1),
        patch("python.installer.tui.curses.color_pair", return_value=0),
    ):
        result_state, _ = draw_device_ids(state, 2, 0, mock_screen, menu_width, device_ids)

    assert "/dev/disk/by-id/ata-DISK1" not in result_state.selected_device_ids


def test_draw_device_ids_selected_device_color() -> None:
    """Test draw_device_ids applies color to already selected devices."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(40)
    state.cursor.set_width(80)
    state.key = 0
    state.selected_device_ids.add("/dev/disk/by-id/ata-DISK1")
    device_ids = {"/dev/disk/by-id/ata-DISK1"}
    menu_width = list(range(0, 60))

    with (
        patch("python.installer.tui.curses.A_BOLD", 1),
        patch("python.installer.tui.curses.color_pair", return_value=7) as mock_color,
    ):
        draw_device_ids(state, 2, 0, mock_screen, menu_width, device_ids)

    mock_screen.attron.assert_any_call(7)


# --- draw_device_menu (lines 396-434) ---


def test_draw_device_menu() -> None:
    """Test draw_device_menu renders devices and calls draw_device_ids."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(40)
    state.cursor.set_width(80)
    state.key = 0

    devices = [
        {"name": "/dev/sda", "size": "100G", "type": "disk", "mountpoints": ""},
    ]
    device_id_mapping = {
        "/dev/sda": {"/dev/disk/by-id/ata-DISK1"},
    }

    with (
        patch("python.installer.tui.curses.color_pair", return_value=0),
        patch("python.installer.tui.curses.A_BOLD", 1),
    ):
        result_state, row_number = draw_device_menu(
            mock_screen, devices, device_id_mapping, state, menu_start_y=0, menu_start_x=0
        )

    assert mock_screen.addstr.call_count > 0
    assert row_number > 0


def test_draw_device_menu_multiple_devices() -> None:
    """Test draw_device_menu with multiple devices."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(40)
    state.cursor.set_width(80)
    state.key = 0

    devices = [
        {"name": "/dev/sda", "size": "100G", "type": "disk", "mountpoints": ""},
        {"name": "/dev/sdb", "size": "200G", "type": "disk", "mountpoints": ""},
    ]
    device_id_mapping = {
        "/dev/sda": {"/dev/disk/by-id/ata-DISK1"},
        "/dev/sdb": {"/dev/disk/by-id/ata-DISK2"},
    }

    with (
        patch("python.installer.tui.curses.color_pair", return_value=0),
        patch("python.installer.tui.curses.A_BOLD", 1),
    ):
        result_state, row_number = draw_device_menu(
            mock_screen, devices, device_id_mapping, state, menu_start_y=0, menu_start_x=0
        )

    # 2 devices + 2 device ids = at least 4 rows past the header
    assert row_number >= 4


def test_draw_device_menu_no_device_ids() -> None:
    """Test draw_device_menu when a device has no IDs."""
    mock_screen = MagicMock()
    state = State()
    state.cursor.set_height(40)
    state.cursor.set_width(80)
    state.key = 0

    devices = [
        {"name": "/dev/sda", "size": "100G", "type": "disk", "mountpoints": ""},
    ]
    device_id_mapping: dict[str, set[str]] = {
        "/dev/sda": set(),
    }

    with (
        patch("python.installer.tui.curses.color_pair", return_value=0),
        patch("python.installer.tui.curses.A_BOLD", 1),
    ):
        result_state, row_number = draw_device_menu(
            mock_screen, devices, device_id_mapping, state, menu_start_y=0, menu_start_x=0
        )

    # Should still work; row_number reflects only the device row (no id rows)
    assert row_number >= 2


# --- draw_menu (lines 447-498) ---


def test_draw_menu_quit_immediately() -> None:
    """Test draw_menu exits when 'q' is pressed immediately."""
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (40, 80)
    mock_screen.getch.return_value = ord("q")

    devices = [
        {"name": "/dev/sda", "size": "100G", "type": "disk", "mountpoints": ""},
    ]
    device_id_mapping = {"/dev/sda": {"/dev/disk/by-id/ata-DISK1"}}

    with (
        patch("python.installer.tui.set_color"),
        patch("python.installer.tui.get_devices", return_value=devices),
        patch("python.installer.tui.get_device_id_mapping", return_value=device_id_mapping),
        patch("python.installer.tui.draw_device_menu", return_value=(State(), 5)),
        patch("python.installer.tui.swap_size_input"),
        patch("python.installer.tui.reserve_size_input"),
        patch("python.installer.tui.status_bar"),
        patch("python.installer.tui.debug_menu"),
        patch("python.installer.tui.curses.color_pair", return_value=0),
    ):
        result = draw_menu(mock_screen)

    assert isinstance(result, State)
    mock_screen.clear.assert_called()
    mock_screen.refresh.assert_called()


def test_draw_menu_navigation_then_quit() -> None:
    """Test draw_menu handles navigation keys before quitting."""
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (40, 80)
    # Simulate pressing down arrow then 'q'
    mock_screen.getch.side_effect = [curses.KEY_DOWN, ord("q")]

    devices = [
        {"name": "/dev/sda", "size": "100G", "type": "disk", "mountpoints": ""},
    ]
    device_id_mapping = {"/dev/sda": set()}

    with (
        patch("python.installer.tui.set_color"),
        patch("python.installer.tui.get_devices", return_value=devices),
        patch("python.installer.tui.get_device_id_mapping", return_value=device_id_mapping),
        patch("python.installer.tui.draw_device_menu", return_value=(State(), 5)),
        patch("python.installer.tui.swap_size_input"),
        patch("python.installer.tui.reserve_size_input"),
        patch("python.installer.tui.status_bar"),
        patch("python.installer.tui.debug_menu"),
        patch("python.installer.tui.curses.color_pair", return_value=0),
    ):
        result = draw_menu(mock_screen)

    assert isinstance(result, State)
