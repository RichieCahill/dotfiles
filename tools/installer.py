"""Install NixOS on a ZFS pool."""

from __future__ import annotations

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


def main() -> None:
    """Main."""
    configure_logger("DEBUG")

    logging.info("Starting installation")

    disks = ("/dev/disk/by-id/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",)

    # Set swap size in GB, set to 1 if you don't want swap to take up too much space
    swap_size = 1
    reserve = 0

    encrypt_key = getenv("ENCRYPT_KEY")

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


if __name__ == "__main__":
    main()
