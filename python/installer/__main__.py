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

from python.common import configure_logger
from python.installer.tui import draw_menu

if TYPE_CHECKING:
    from collections.abc import Sequence


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
    process = Popen(command.split(), stdout=PIPE, stderr=PIPE)
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
        pool_disks (Sequence[str]): A tuple of disks to use for the pool.
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
        "-O mountpoint=legacy "
        "-O compression=zstd "
        "-O atime=off "
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
    bash_wrapper("zfs create -o canmount=noauto -o reservation=10G root_pool/root")
    bash_wrapper("zfs create root_pool/home")
    bash_wrapper("zfs create root_pool/var -o reservation=1G")
    bash_wrapper("zfs create -o compression=zstd-9 -o reservation=10G root_pool/nix")
    datasets = bash_wrapper("zfs list -o name")

    expected_datasets = {
        "root_pool/root",
        "root_pool/home",
        "root_pool/var",
        "root_pool/nix",
    }
    missing_datasets = expected_datasets.difference(datasets.splitlines())
    if missing_datasets:
        logging.critical(f"Failed to create pools {missing_datasets}")
        sys.exit(1)


def get_cpu_manufacturer() -> str:
    """Get the CPU manufacturer."""
    output = bash_wrapper("cat /proc/cpuinfo")

    id_vendor = {"AuthenticAMD": "amd", "GenuineIntel": "intel"}

    for line in output.splitlines():
        if "vendor_id" in line:
            return id_vendor[line.split(": ")[1].strip()]

    error = "Failed to get CPU manufacturer"
    raise RuntimeError(error)


def get_boot_drive_id(disk: str) -> str:
    """Get the boot drive ID."""
    output = bash_wrapper(f"lsblk -o UUID {disk}-part1")
    return output.splitlines()[1]


def create_nix_hardware_file(mnt_dir: str, disks: Sequence[str], encrypt: str | None) -> None:
    """Create a NixOS hardware file."""
    cpu_manufacturer = get_cpu_manufacturer()

    devices = ""
    if encrypt:
        disk = disks[0]

        devices = (
            f'     luks.devices."luks-root-pool-{disk.split("/")[-1]}-part2"'
            "= {\n"
            f'        device = "{disk}-part2";\n'
            "        bypassWorkqueues = true;\n"
            "        allowDiscards = true;\n"
            "      };\n"
        )

    host_id = format(getrandbits(32), "08x")

    nix_hardware = (
        "{ config, lib, modulesPath, ... }:\n"
        "{\n"
        '  imports = [ (modulesPath + "/installer/scan/not-detected.nix") ];\n\n'
        "  boot = {\n"
        "    initrd = {\n"
        '      availableKernelModules = [ \n        "ahci"\n        "ehci_pci"\n        "nvme"\n        "sd_mod"\n'
        '        "usb_storage"\n        "usbhid"\n        "xhci_pci"\n      ];\n'
        "      kernelModules = [ ];\n"
        f" {devices}"
        "    };\n"
        f'    kernelModules = [ "kvm-{cpu_manufacturer}" ];\n'
        "    extraModulePackages = [ ];\n"
        "  };\n\n"
        "  fileSystems = {\n"
        '    "/" = lib.mkDefault {\n      device = "root_pool/root";\n      fsType = "zfs";\n    };\n\n'
        '    "/home" = {\n      device = "root_pool/home";\n      fsType = "zfs";\n    };\n\n'
        '    "/var" = {\n      device = "root_pool/var";\n      fsType = "zfs";\n    };\n\n'
        '    "/nix" = {\n      device = "root_pool/nix";\n      fsType = "zfs";\n    };\n\n'
        '    "/boot" = {\n'
        f'      device = "/dev/disk/by-uuid/{get_boot_drive_id(disks[0])}";\n'
        '      fsType = "vfat";\n      options = [\n        "fmask=0077"\n'
        '        "dmask=0077"\n      ];\n    };\n  };\n\n'
        "  swapDevices = [ ];\n\n"
        "  networking.useDHCP = lib.mkDefault true;\n\n"
        '  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";\n'
        f"  hardware.cpu.{cpu_manufacturer}.updateMicrocode = "
        "lib.mkDefault config.hardware.enableRedistributableFirmware;\n"
        f'  networking.hostId = "{host_id}";\n'
        "}\n"
    )

    Path(f"{mnt_dir}/etc/nixos/hardware-configuration.nix").write_text(nix_hardware)


def install_nixos(mnt_dir: str, disks: Sequence[str], encrypt: str | None) -> None:
    """Install NixOS."""
    bash_wrapper(f"mount -o X-mount.mkdir -t zfs root_pool/root {mnt_dir}")
    bash_wrapper(f"mount -o X-mount.mkdir -t zfs root_pool/home {mnt_dir}/home")
    bash_wrapper(f"mount -o X-mount.mkdir -t zfs root_pool/var {mnt_dir}/var")
    bash_wrapper(f"mount -o X-mount.mkdir -t zfs root_pool/nix {mnt_dir}/nix")

    for disk in disks:
        bash_wrapper(f"mkfs.vfat -n EFI {disk}-part1")

    # set up mirroring afterwards if more than one disk
    boot_partition = (
        f"mount -t vfat -o fmask=0077,dmask=0077,iocharset=iso8859-1,X-mount.mkdir {disks[0]}-part1 {mnt_dir}/boot"
    )
    bash_wrapper(boot_partition)

    bash_wrapper(f"nixos-generate-config --root {mnt_dir}")

    create_nix_hardware_file(mnt_dir, disks, encrypt)

    run(("nixos-install", "--root", mnt_dir), check=True)


def installer(
    disks: Sequence[str],
    swap_size: int,
    reserve: int,
    encrypt_key: str | None,
) -> None:
    """Main."""
    logging.info("Starting installation")

    for disk in disks:
        partition_disk(disk, swap_size, reserve)

        test = Popen(("printf", f"'{encrypt_key}'"), stdout=PIPE)
        if encrypt_key:
            sleep(1)
            for command in (
                f"cryptsetup luksFormat --type luks2 {disk}-part2 -",
                f"cryptsetup luksOpen {disk}-part2 luks-root-pool-{disk.split('/')[-1]}-part2 -",
            ):
                run(command, check=True, stdin=test.stdout)

    mnt_dir = "/tmp/nix_install"  # noqa: S108

    Path(mnt_dir).mkdir(parents=True, exist_ok=True)

    if encrypt_key:
        pool_disks = [f"/dev/mapper/luks-root-pool-{disk.split('/')[-1]}-part2" for disk in disks]
    else:
        pool_disks = [f"{disk}-part2" for disk in disks]

    create_zfs_pool(pool_disks, mnt_dir)

    create_zfs_datasets()

    install_nixos(mnt_dir, disks, encrypt_key)

    logging.info("Installation complete")


def main() -> None:
    """Main."""
    configure_logger("DEBUG")

    state = curses.wrapper(draw_menu)

    encrypt_key = getenv("ENCRYPT_KEY")

    logging.info("installing_nixos")
    logging.info(f"disks: {state.selected_device_ids}")
    logging.info(f"swap_size: {state.swap_size}")
    logging.info(f"reserve: {state.reserve_size}")
    logging.info(f"encrypted: {bool(encrypt_key)}")

    sleep(3)

    installer(
        disks=state.get_selected_devices(),
        swap_size=state.swap_size,
        reserve=state.reserve_size,
        encrypt_key=encrypt_key,
    )


if __name__ == "__main__":
    main()
