"""Install NixOS on a ZFS pool."""

from __future__ import annotations

import curses
import logging
import sys
from os import getenv
from pathlib import Path
from random import getrandbits
from subprocess import PIPE, Popen, run
from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def configure_logger(level: str = "INFO") -> None:
    """Configure the logger.
    Args:
        level (str, optional): The logging level. Defaults to "INFO".
    """
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def bash_wrapper(command: str) -> str:
    """Execute a bash command and capture the output.
    Args:
        command (str): The bash command to be executed.
    Returns:
        Tuple[str, int]: A tuple containing the output of the command (stdout) as a string,
        the error output (stderr) as a string (optional), and the return code as an integer.
    """
    logging.debug(f"running {command=}")
    # This is a acceptable risk
    process = Popen(command.split(), stdout=PIPE, stderr=PIPE)  # noqa: S603
    output, _ = process.communicate()
    if process.returncode != 0:
        error = f"Failed to run command {command=} return code {process.returncode=}"
        raise RuntimeError(error)

    return output.decode()


def partition_disk(disk: str, swap_size: int, reserve: int = 0) -> None:
    """Partition a disk.
    Args:
        disk (str): The disk to partition.
        swap_size (int): The size of the swap partition in GB.
            minimum value is 1.
        reserve (int, optional): The size of the reserve partition in GB. Defaults to 0.
            minimum value is 0.
    """
    logging.info(f"partitioning {disk=}")
    swap_size = max(swap_size, 1)
    reserve = max(reserve, 0)

    bash_wrapper(f"blkdiscard -f {disk}")

    if reserve > 0:
        msg = f"Creating swap partition on {disk=} with size {swap_size=}GiB and reserve {reserve=}GiB"
        logging.info(msg)

        swap_start = swap_size + reserve
        swap_partition = f"mkpart swap -{swap_start}GiB -{reserve}GiB "
    else:
        logging.info(f"Creating swap partition on {disk=} with size {swap_size=}GiB")
        swap_start = swap_size
        swap_partition = f"mkpart swap -{swap_start}GiB 100% "

    logging.debug(f"{swap_partition=}")

    create_partitions = (
        f"parted --script --align=optimal {disk} -- "
        "mklabel gpt "
        "mkpart EFI 1MiB 4GiB "
        f"mkpart root_pool 4GiB -{swap_start}GiB "
        f"{swap_partition}"
        "set 1 esp on"
    )
    bash_wrapper(create_partitions)

    logging.info(f"{disk=} successfully partitioned")


def create_zfs_pool(pool_disks: Sequence[str], mnt_dir: str) -> None:
    """Create a ZFS pool.
    Args:
        disks (Sequence[str]): A tuple of disks to use for the pool.
        mnt_dir (str): The mount directory.
    """
    if len(pool_disks) <= 0:
        error = "disks must be a tuple of at least length 1"
        raise ValueError(error)

    zpool_create = (
        "zpool create "
        "-o ashift=12 "
        "-o autotrim=on "
        f"-R {mnt_dir} "
        "-O acltype=posixacl "
        "-O canmount=off "
        "-O dnodesize=auto "
        "-O normalization=formD "
        "-O relatime=on "
        "-O xattr=sa "
        "-O mountpoint=none "
        "-O primarycache=metadata "
        "-O compression=zstd "
        "root_pool "
    )
    if len(pool_disks) == 1:
        zpool_create += pool_disks[0]
    else:
        zpool_create += "mirror "
        zpool_create += " ".join(pool_disks)

    bash_wrapper(zpool_create)
    zpools = bash_wrapper("zpool list -o name")
    if "root_pool" not in zpools.splitlines():
        logging.critical("Failed to create root_pool")
        sys.exit(1)


def create_zfs_datasets() -> None:
    """Create ZFS datasets."""
    default_options = "-o compression=zstd -o atime=off -o mountpoint=legacy"

    bash_wrapper(f"zfs create {default_options} -o canmount=noauto root_pool/root")
    for dataset in ("home", "var"):
        bash_wrapper(f"zfs create {default_options} root_pool/{dataset}")

    datasets = bash_wrapper("zfs list -o name")

    expected_datasets = {"root_pool/root", "root_pool/home", "root_pool/var"}
    missing_datasets = expected_datasets.difference(datasets.splitlines())
    if missing_datasets:
        logging.critical(f"Failed to create pools {missing_datasets}")
        sys.exit(1)


def install_nixos(mnt_dir: str, disks: Sequence[str], encrypt: bool) -> None:
    """Install NixOS."""
    bash_wrapper(f"mount -o X-mount.mkdir -t zfs root_pool/root {mnt_dir}")
    bash_wrapper(f"mount -o X-mount.mkdir -t zfs root_pool/home {mnt_dir}/home")
    bash_wrapper(f"mount -o X-mount.mkdir -t zfs root_pool/var {mnt_dir}/var")

    for disk in disks:
        bash_wrapper(f"mkfs.vfat -n EFI {disk}-part1")

    # set up mirroring afterwards if more than one disk
    boot_partition = f"mount -t vfat -o fmask=0077,dmask=0077,iocharset=iso8859-1,X-mount.mkdir {disks[0]}-part1 {mnt_dir}/boot"
    bash_wrapper(boot_partition)

    bash_wrapper(f"nixos-generate-config --root {mnt_dir}")

    host_id = format(getrandbits(32), "08x")

    nix_hardware = Path(f"{mnt_dir}/etc/nixos/hardware-configuration.nix").read_text()
    nix_hardware = nix_hardware.replace(
        ";\n}", f';\n  networking.hostId = "{host_id}";' "\n}"
    )

    if encrypt:
        test = [
            f'    "luks-root-pool-{disk.split("/")[-1]}-part2".device = "{disk}-part2";\n'
            for disk in disks
        ]

        encrypted_disks = (
            ";\n  boot.initrd.luks.devices = {\n" f"{''.join(test)}" "  };\n" "}"
        )
        nix_hardware = nix_hardware.replace(";\n}", encrypted_disks)

    Path(f"{mnt_dir}/etc/nixos/hardware-configuration.nix").write_text(nix_hardware)

    run(("nixos-install", "--root", mnt_dir), check=True)  # noqa: S603


def installer(
    disks: set[str],
    swap_size: int,
    reserve: int,
    encrypt_key: str | None,
) -> None:
    """Main."""
    logging.info("Starting installation")

    for disk in disks:
        partition_disk(disk, swap_size, reserve)

        if encrypt_key:
            sleep(1)
            for command in (
                f'printf "{encrypt_key}" | cryptsetup luksFormat --type luks2 {disk}-part2 -',
                f'printf "{encrypt_key}" | cryptsetup luksOpen {disk}-part2 luks-root-pool-{disk.split("/")[-1]}-part2 -',
            ):
                run(command, shell=True, check=True)

    mnt_dir = "/tmp/nix_install"  # noqa: S108

    Path(mnt_dir).mkdir(parents=True, exist_ok=True)

    if encrypt_key:
        pool_disks = [
            f'/dev/mapper/luks-root-pool-{disk.split("/")[-1]}-part2' for disk in disks
        ]
    else:
        pool_disks = [f"{disk}-part2" for disk in disks]

    create_zfs_pool(pool_disks, mnt_dir)

    create_zfs_datasets()

    install_nixos(mnt_dir, disks, encrypt_key)

    logging.info("Installation complete")


class Cursor:
    def __init__(self):
        self.x_position = 0
        self.y_position = 0
        self.height = 0
        self.width = 0

    def set_height(self, height: int):
        self.height = height

    def set_width(self, width: int):
        self.width = width

    def x_bounce_check(self, cursor: int) -> int:
        cursor = max(0, cursor)
        return min(self.width - 1, cursor)

    def y_bounce_check(self, cursor: int) -> int:
        cursor = max(0, cursor)
        return min(self.height - 1, cursor)

    def set_x(self, x: int):
        self.x_position = self.x_bounce_check(x)

    def set_y(self, y: int):
        self.y_position = self.y_bounce_check(y)

    def get_x(self) -> int:
        return self.x_position

    def get_y(self) -> int:
        return self.y_position

    def move_up(self):
        self.set_y(self.y_position - 1)

    def move_down(self):
        self.set_y(self.y_position + 1)

    def move_left(self):
        self.set_x(self.x_position - 1)

    def move_right(self):
        self.set_x(self.x_position + 1)

    def navigation(self, key: int) -> None:
        action = {
            curses.KEY_DOWN: self.move_down,
            curses.KEY_UP: self.move_up,
            curses.KEY_RIGHT: self.move_right,
            curses.KEY_LEFT: self.move_left,
        }

        action.get(key, lambda: None)()


class State:
    def __init__(self):
        self.key = 0
        self.cursor = Cursor()

        self.swap_size = 0
        self.show_swap_input = False

        self.reserve_size = 0
        self.show_reserve_input = False

        self.selected_devices = set()


def get_device(raw_device: str) -> dict[str, str]:
    raw_device_components = raw_device.split(" ")
    return {
        thing.split("=")[0].lower(): thing.split("=")[1].strip('"')
        for thing in raw_device_components
    }


def get_devices() -> list[dict[str, str]]:
    """Get a list of devices."""
    # --bytes
    raw_devices = bash_wrapper("lsblk --paths --pairs").splitlines()
    return [get_device(raw_device) for raw_device in raw_devices]


def calculate_device_menu_padding(
    devices: list[dict[str, str]], column: str, padding: int = 0
) -> int:
    return max(len(device[column]) for device in devices) + padding


def draw_device_menu(
    std_screen: curses.window,
    devices: list[dict[str, str]],
    state: State,
    menu_start_y: int = 0,
    menu_start_x: int = 0,
) -> State:
    padding = 2

    name_padding = calculate_device_menu_padding(devices, "name", padding)
    size_padding = calculate_device_menu_padding(devices, "size", padding)
    type_padding = calculate_device_menu_padding(devices, "type", padding)
    mountpoints_padding = calculate_device_menu_padding(devices, "mountpoints", padding)

    device_header = f"{"Name":{name_padding}}{"Size":{size_padding}}{"Type":{type_padding}}{"Mountpoints":{mountpoints_padding}}"

    menu_width = range(menu_start_x, len(device_header) + menu_start_x)

    std_screen.addstr(menu_start_y, menu_start_x, device_header, curses.color_pair(5))
    devises_list_start = menu_start_y + 1

    for index, device in enumerate(devices):
        device_row_y = devises_list_start + index
        device_row = (
            f"{device['name']:{name_padding}}"
            f"{device['size']:{size_padding}}"
            f"{device['type']:{type_padding}}"
            f"{device['mountpoints']:{mountpoints_padding}}"
        )

        if device_row_y == state.cursor.get_y() and state.cursor.get_x() in menu_width:
            std_screen.attron(curses.A_BOLD)
            if state.key == ord(" "):
                if device["name"] not in state.selected_devices:
                    state.selected_devices.add(device["name"])
                else:
                    state.selected_devices.remove(device["name"])

        if device["name"] in state.selected_devices:
            std_screen.attron(curses.color_pair(7))

        std_screen.addstr(device_row_y, menu_start_x, device_row)

        std_screen.attroff(curses.color_pair(7))
        std_screen.attroff(curses.A_BOLD)

    return state


def debug_menu(std_screen: curses.window, key: int) -> None:
    height, width = std_screen.getmaxyx()
    width_height = "Width: {}, Height: {}".format(width, height)
    std_screen.addstr(height - 4, 0, width_height, curses.color_pair(5))

    key_pressed = f"Last key pressed: {key}"[: width - 1]
    if key == 0:
        key_pressed = "No key press detected..."[: width - 1]
    std_screen.addstr(height - 3, 0, key_pressed)

    for i in range(0, 8):
        std_screen.addstr(height - 2, i * 3, f"{i}██", curses.color_pair(i))


def status_bar(
    std_screen: curses.window,
    cursor: Cursor,
    width: int,
    height: int,
) -> None:
    std_screen.attron(curses.A_REVERSE)
    std_screen.attron(curses.color_pair(3))

    status_bar = (
        f"Press 'q' to exit | STATUS BAR | Pos: {cursor.get_x()}, {cursor.get_y()}"
    )
    std_screen.addstr(height - 1, 0, status_bar)
    std_screen.addstr(height - 1, len(status_bar), " " * (width - len(status_bar) - 1))

    std_screen.attroff(curses.color_pair(3))
    std_screen.attroff(curses.A_REVERSE)


def set_color() -> None:
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)


def get_text_input(std_screen: curses.window, prompt: str, y: int, x: int) -> str:
    curses.echo()
    std_screen.addstr(y, x, prompt)
    input_str = ""
    while True:
        key = std_screen.getch()
        if key == ord("\n"):
            break
        elif key == 27:  # ESC key
            input_str = ""
            break
        elif key in (curses.KEY_BACKSPACE, ord("\b"), 127):
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
            std_screen.addstr(
                swap_offset, 0, "Invalid input. Press any key to continue."
            )
            std_screen.getch()
            state.show_swap_input = False

    return state


def reserve_size_input(
    std_screen: curses.window,
    state: State,
    reserve_offset: int,
) -> State:
    reserve_size_text = "reserve size (GB): "
    std_screen.addstr(reserve_offset, 0, f"{reserve_size_text}{state.reserve_size}")
    if state.key == ord("\n") and state.cursor.get_y() == reserve_offset:
        state.show_reserve_input = True

    if state.show_reserve_input:
        reserve_size_str = get_text_input(
            std_screen, reserve_size_text, reserve_offset, 0
        )
        try:
            state.reserve_size = int(reserve_size_str)
            state.show_reserve_input = False
        except ValueError:
            std_screen.addstr(
                reserve_offset, 0, "Invalid input. Press any key to continue."
            )
            std_screen.getch()
            state.show_reserve_input = False

    return state


def draw_menu(std_screen: curses.window) -> State:
    # Clear and refresh the screen for a blank canvas
    std_screen.clear()
    std_screen.refresh()

    set_color()

    state = State()

    devices = get_devices()

    # Loop where k is the last character pressed
    while state.key != ord("q"):
        std_screen.clear()
        height, width = std_screen.getmaxyx()

        state.cursor.set_height(height)
        state.cursor.set_width(width)

        state.cursor.navigation(state.key)

        state = draw_device_menu(
            std_screen=std_screen,
            state=state,
            devices=devices,
        )

        device_count = len(devices)

        swap_offset = device_count + 2

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


def main() -> None:
    configure_logger("DEBUG")

    state = curses.wrapper(draw_menu)

    encrypt_key = getenv("ENCRYPT_KEY")

    logging.info("installing_nixos")
    logging.info(f"disks: {state.selected_devices}")
    logging.info(f"swap_size: {state.swap_size}")
    logging.info(f"reserve: {state.reserve_size}")
    logging.info(f"encrypted: {bool(encrypt_key)}")

    installer(
        disks=state.selected_devices,
        swap_size=state.swap_size,
        reserve=state.reserve_size,
        encrypt_key=encrypt_key,
    )


if __name__ == "__main__":
    main()
