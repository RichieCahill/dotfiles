"""TUI module."""

from __future__ import annotations

import curses
import logging
from collections import defaultdict
from subprocess import PIPE, Popen

logger = logging.getLogger(__name__)


def bash_wrapper(command: str) -> str:
    """Execute a bash command and capture the output.

    Args:
        command (str): The bash command to be executed.

    Returns:
        Tuple[str, int]: A tuple containing the output of the command (stdout) as a string,
        the error output (stderr) as a string (optional), and the return code as an integer.
    """
    logger.debug(f"running {command=}")
    # This is a acceptable risk
    process = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    output, _ = process.communicate()
    if process.returncode != 0:
        error = f"Failed to run command {command=} return code {process.returncode=}"
        raise RuntimeError(error)

    return output.decode()


class Cursor:
    """Cursor class."""

    def __init__(self) -> None:
        """Initialize the Cursor class."""
        self.x_position = 0
        self.y_position = 0
        self.height = 0
        self.width = 0

    def set_height(self, height: int) -> None:
        """Set height."""
        self.height = height

    def set_width(self, width: int) -> None:
        """Set width."""
        self.width = width

    def x_bounce_check(self, cursor: int) -> int:
        """X bounce check."""
        cursor = max(0, cursor)
        return min(self.width - 1, cursor)

    def y_bounce_check(self, cursor: int) -> int:
        """Y bounce check."""
        cursor = max(0, cursor)
        return min(self.height - 1, cursor)

    def set_x(self, x: int) -> None:
        """Set x."""
        self.x_position = self.x_bounce_check(x)

    def set_y(self, y: int) -> None:
        """Set y."""
        self.y_position = self.y_bounce_check(y)

    def get_x(self) -> int:
        """Get x."""
        return self.x_position

    def get_y(self) -> int:
        """Get y."""
        return self.y_position

    def move_up(self) -> None:
        """Move up."""
        self.set_y(self.y_position - 1)

    def move_down(self) -> None:
        """Move down."""
        self.set_y(self.y_position + 1)

    def move_left(self) -> None:
        """Move left."""
        self.set_x(self.x_position - 1)

    def move_right(self) -> None:
        """Move right."""
        self.set_x(self.x_position + 1)

    def navigation(self, key: int) -> None:
        """Navigation.

        Args:
            key (int): The key.
        """
        action = {
            curses.KEY_DOWN: self.move_down,
            curses.KEY_UP: self.move_up,
            curses.KEY_RIGHT: self.move_right,
            curses.KEY_LEFT: self.move_left,
        }

        action.get(key, lambda: None)()


class State:
    """State class to store the state of the program."""

    def __init__(self) -> None:
        """Initialize the State class."""
        self.key = 0
        self.cursor = Cursor()

        self.swap_size = 0
        self.show_swap_input = False

        self.reserve_size = 0
        self.show_reserve_input = False

        self.selected_device_ids: set[str] = set()

    def get_selected_devices(self) -> tuple[str, ...]:
        """Get selected devices."""
        return tuple(self.selected_device_ids)


def get_device(raw_device: str) -> dict[str, str]:
    """Get a device.

    Args:
        raw_device (str): The raw device.

    Returns:
        dict[str, str]: The device.
    """
    raw_device_components = raw_device.split(" ")
    return {thing.split("=")[0].lower(): thing.split("=")[1].strip('"') for thing in raw_device_components}


def get_devices() -> list[dict[str, str]]:
    """Get a list of devices."""
    # --bytes
    raw_devices = bash_wrapper("lsblk --paths --pairs").splitlines()
    return [get_device(raw_device) for raw_device in raw_devices]


def set_color() -> None:
    """Set the color."""
    curses.start_color()
    curses.use_default_colors()
    for i in range(curses.COLORS):
        curses.init_pair(i + 1, i, -1)


def debug_menu(std_screen: curses.window, key: int) -> None:
    """Debug menu.

    Args:
        std_screen (curses.window): The curses window.
        key (int): The key.
    """
    height, width = std_screen.getmaxyx()
    std_screen.addstr(height - 4, 0, f"Width: {width}, Height: {height}", curses.color_pair(5))

    key_pressed = f"Last key pressed: {key}"[: width - 1]
    if key == 0:
        key_pressed = "No key press detected..."[: width - 1]
    std_screen.addstr(height - 3, 0, key_pressed)

    for i in range(8):
        std_screen.addstr(height - 2, i * 3, f"{i}██", curses.color_pair(i))


def get_text_input(std_screen: curses.window, prompt: str, y: int, x: int) -> str:
    """Get text input.

    Args:
        std_screen (curses.window): The curses window.
        prompt (str): The prompt.
        y (int): The y position.
        x (int): The x position.

    Returns:
        str: The input string.
    """
    esc_key = 27
    curses.echo()
    std_screen.addstr(y, x, prompt)
    input_str = ""
    while True:
        key = std_screen.getch()
        if key == ord("\n"):
            break
        if key == esc_key:
            input_str = ""
            break
        if key in (curses.KEY_BACKSPACE, ord("\b"), 127):
            input_str = input_str[:-1]
            std_screen.addstr(y, x + len(prompt), input_str + " ")
        else:
            input_str += chr(key)
        std_screen.refresh()
    curses.noecho()
    return input_str


def swap_size_input(
    std_screen: curses.window,
    state: State,
    swap_offset: int,
) -> State:
    """Reserve size input.

    Args:
        std_screen (curses.window): The curses window.
        state (State): The state object.
        swap_offset (int): The swap offset.

    Returns:
        State: The updated state object.
    """
    swap_size_text = "Swap size (GB): "
    std_screen.addstr(swap_offset, 0, f"{swap_size_text}{state.swap_size}")
    if state.key == ord("\n") and state.cursor.get_y() == swap_offset:
        state.show_swap_input = True

    if state.show_swap_input:
        swap_size_str = get_text_input(std_screen, swap_size_text, swap_offset, 0)
        try:
            state.swap_size = int(swap_size_str)
            state.show_swap_input = False
        except ValueError:
            std_screen.addstr(swap_offset, 0, "Invalid input. Press any key to continue.")
            std_screen.getch()
            state.show_swap_input = False

    return state


def reserve_size_input(
    std_screen: curses.window,
    state: State,
    reserve_offset: int,
) -> State:
    """Reserve size input.

    Args:
        std_screen (curses.window): The curses window.
        state (State): The state object.
        reserve_offset (int): The reserve offset.

    Returns:
        State: The updated state object.
    """
    reserve_size_text = "reserve size (GB): "
    std_screen.addstr(reserve_offset, 0, f"{reserve_size_text}{state.reserve_size}")
    if state.key == ord("\n") and state.cursor.get_y() == reserve_offset:
        state.show_reserve_input = True

    if state.show_reserve_input:
        reserve_size_str = get_text_input(std_screen, reserve_size_text, reserve_offset, 0)
        try:
            state.reserve_size = int(reserve_size_str)
            state.show_reserve_input = False
        except ValueError:
            std_screen.addstr(reserve_offset, 0, "Invalid input. Press any key to continue.")
            std_screen.getch()
            state.show_reserve_input = False

    return state


def status_bar(
    std_screen: curses.window,
    cursor: Cursor,
    width: int,
    height: int,
) -> None:
    """Draw the status bar.

    Args:
        std_screen (curses.window): The curses window.
        cursor (Cursor): The cursor.
        width (int): The width.
        height (int): The height.
    """
    std_screen.attron(curses.A_REVERSE)
    std_screen.attron(curses.color_pair(3))

    status_bar = f"Press 'q' to exit | STATUS BAR | Pos: {cursor.get_x()}, {cursor.get_y()}"
    std_screen.addstr(height - 1, 0, status_bar)
    std_screen.addstr(height - 1, len(status_bar), " " * (width - len(status_bar) - 1))

    std_screen.attroff(curses.color_pair(3))
    std_screen.attroff(curses.A_REVERSE)


def get_device_id_mapping() -> dict[str, set[str]]:
    """Get a list of device ids.

    Returns:
        list[str]: the list of device ids
    """
    device_ids = bash_wrapper("find /dev/disk/by-id -type l").splitlines()

    device_id_mapping: dict[str, set[str]] = defaultdict(set)

    for device_id in device_ids:
        device = bash_wrapper(f"readlink -f {device_id}").strip()
        device_id_mapping[device].add(device_id)

    return device_id_mapping


def calculate_device_menu_padding(devices: list[dict[str, str]], column: str, padding: int = 0) -> int:
    """Calculate the device menu padding.

    Args:
        devices (list[dict[str, str]]): The devices.
        column (str): The column.
        padding (int, optional): The padding. Defaults to 0.

    Returns:
        int: The calculated padding.
    """
    return max(len(device[column]) for device in devices) + padding


def draw_device_ids(
    state: State,
    row_number: int,
    menu_start_x: int,
    std_screen: curses.window,
    menu_width: list[int],
    device_ids: set[str],
) -> tuple[State, int]:
    """Draw device IDs.

    Args:
        state (State): The state object.
        row_number (int): The row number.
        menu_start_x (int): The menu start x.
        std_screen (curses.window): The curses window.
        menu_width (list[int]): The menu width.
        device_ids (set[str]): The device IDs.

    Returns:
        tuple[State, int]: The updated state object and the row number.
    """
    for device_id in sorted(device_ids):
        row_number = row_number + 1
        if row_number == state.cursor.get_y() and state.cursor.get_x() in menu_width:
            std_screen.attron(curses.A_BOLD)
            if state.key == ord(" "):
                if device_id not in state.selected_device_ids:
                    state.selected_device_ids.add(device_id)
                else:
                    state.selected_device_ids.remove(device_id)

        if device_id in state.selected_device_ids:
            std_screen.attron(curses.color_pair(7))

        std_screen.addstr(row_number, menu_start_x, f"  {device_id}")

        std_screen.attroff(curses.color_pair(7))
        std_screen.attroff(curses.A_BOLD)

    return state, row_number


def draw_device_menu(
    std_screen: curses.window,
    devices: list[dict[str, str]],
    device_id_mapping: dict[str, set[str]],
    state: State,
    menu_start_y: int = 0,
    menu_start_x: int = 0,
) -> tuple[State, int]:
    """Draw the device menu and handle user input.

    Args:
        std_screen (curses.window): the curses window to draw on
        devices (list[dict[str, str]]): the list of devices to draw
        device_id_mapping (dict[str, set[str]]): the list of device ids to draw
        state (State): the state object to update
        menu_start_y (int, optional): the y position to start drawing the menu. Defaults to 0.
        menu_start_x (int, optional): the x position to start drawing the menu. Defaults to 0.

    Returns:
        State: the updated state object
    """
    padding = 2

    name_padding = calculate_device_menu_padding(devices, "name", padding)
    size_padding = calculate_device_menu_padding(devices, "size", padding)
    type_padding = calculate_device_menu_padding(devices, "type", padding)
    mountpoints_padding = calculate_device_menu_padding(devices, "mountpoints", padding)

    device_header = (
        f"{'Name':{name_padding}}{'Size':{size_padding}}{'Type':{type_padding}}{'Mountpoints':{mountpoints_padding}}"
    )

    menu_width = list(range(menu_start_x, len(device_header) + menu_start_x))

    std_screen.addstr(menu_start_y, menu_start_x, device_header, curses.color_pair(5))
    devises_list_start = menu_start_y + 1

    row_number = devises_list_start

    for device in devices:
        row_number = row_number + 1
        device_name = device["name"]
        device_row = (
            f"{device_name:{name_padding}}"
            f"{device['size']:{size_padding}}"
            f"{device['type']:{type_padding}}"
            f"{device['mountpoints']:{mountpoints_padding}}"
        )
        std_screen.addstr(row_number, menu_start_x, device_row)

        state, row_number = draw_device_ids(
            state=state,
            row_number=row_number,
            menu_start_x=menu_start_x,
            std_screen=std_screen,
            menu_width=menu_width,
            device_ids=device_id_mapping[device_name],
        )

    return state, row_number


def draw_menu(std_screen: curses.window) -> State:
    """Draw the menu and handle user input.

    Args:
        std_screen (curses.window): the curses window to draw on

    Returns:
        State: the state object
    """
    # Clear and refresh the screen for a blank canvas
    std_screen.clear()
    std_screen.refresh()

    set_color()

    state = State()

    devices = get_devices()

    device_id_mapping = get_device_id_mapping()

    # Loop where k is the last character pressed
    while state.key != ord("q"):
        std_screen.clear()
        height, width = std_screen.getmaxyx()

        state.cursor.set_height(height)
        state.cursor.set_width(width)

        state.cursor.navigation(state.key)

        state, device_menu_size = draw_device_menu(
            std_screen=std_screen,
            state=state,
            devices=devices,
            device_id_mapping=device_id_mapping,
        )

        swap_offset = device_menu_size + 2

        swap_size_input(
            std_screen=std_screen,
            state=state,
            swap_offset=swap_offset,
        )
        reserve_size_input(
            std_screen=std_screen,
            state=state,
            reserve_offset=swap_offset + 1,
        )

        status_bar(std_screen, state.cursor, width, height)

        debug_menu(std_screen, state.key)

        std_screen.move(state.cursor.get_y(), state.cursor.get_x())

        std_screen.refresh()

        state.key = std_screen.getch()

    return state
