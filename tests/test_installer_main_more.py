"""Additional tests for python/installer/__main__.py covering missing lines."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from python.installer.__main__ import (
    create_nix_hardware_file,
    install_nixos,
    installer,
    main,
)


# --- create_nix_hardware_file (lines 167-218) ---


def test_create_nix_hardware_file_no_encrypt() -> None:
    """Test create_nix_hardware_file without encryption."""
    with (
        patch("python.installer.__main__.get_cpu_manufacturer", return_value="amd"),
        patch("python.installer.__main__.get_boot_drive_id", return_value="ABCD-1234"),
        patch("python.installer.__main__.getrandbits", return_value=0xDEADBEEF),
        patch("python.installer.__main__.Path") as mock_path,
    ):
        create_nix_hardware_file("/mnt", ["/dev/sda"], encrypt=None)

    mock_path.assert_called_once_with("/mnt/etc/nixos/hardware-configuration.nix")
    written_content = mock_path.return_value.write_text.call_args[0][0]
    assert "kvm-amd" in written_content
    assert "ABCD-1234" in written_content
    assert "deadbeef" in written_content
    assert "luks" not in written_content


def test_create_nix_hardware_file_with_encrypt() -> None:
    """Test create_nix_hardware_file with encryption enabled."""
    with (
        patch("python.installer.__main__.get_cpu_manufacturer", return_value="intel"),
        patch("python.installer.__main__.get_boot_drive_id", return_value="EFGH-5678"),
        patch("python.installer.__main__.getrandbits", return_value=0x12345678),
        patch("python.installer.__main__.Path") as mock_path,
    ):
        create_nix_hardware_file("/mnt", ["/dev/sda"], encrypt="mykey")

    written_content = mock_path.return_value.write_text.call_args[0][0]
    assert "kvm-intel" in written_content
    assert "EFGH-5678" in written_content
    assert "12345678" in written_content
    assert "luks" in written_content
    assert "luks-root-pool-sda-part2" in written_content
    assert "bypassWorkqueues" in written_content
    assert "allowDiscards" in written_content


def test_create_nix_hardware_file_content_structure() -> None:
    """Test create_nix_hardware_file generates correct Nix structure."""
    with (
        patch("python.installer.__main__.get_cpu_manufacturer", return_value="amd"),
        patch("python.installer.__main__.get_boot_drive_id", return_value="UUID-1234"),
        patch("python.installer.__main__.getrandbits", return_value=0xAABBCCDD),
        patch("python.installer.__main__.Path") as mock_path,
    ):
        create_nix_hardware_file("/mnt", ["/dev/sda"], encrypt=None)

    written_content = mock_path.return_value.write_text.call_args[0][0]
    assert "{ config, lib, modulesPath, ... }:" in written_content
    assert "boot =" in written_content
    assert "fileSystems" in written_content
    assert "root_pool/root" in written_content
    assert "root_pool/home" in written_content
    assert "root_pool/var" in written_content
    assert "root_pool/nix" in written_content
    assert "networking.hostId" in written_content
    assert "x86_64-linux" in written_content


# --- install_nixos (lines 221-241) ---


def test_install_nixos_single_disk() -> None:
    """Test install_nixos mounts filesystems and runs nixos-install."""
    with (
        patch("python.installer.__main__.bash_wrapper") as mock_bash,
        patch("python.installer.__main__.run") as mock_run,
        patch("python.installer.__main__.create_nix_hardware_file") as mock_hw,
    ):
        install_nixos("/mnt", ["/dev/sda"], encrypt=None)

    # 4 mount commands + 1 mkfs.vfat + 1 boot mount + 1 nixos-generate-config = 7 bash_wrapper calls
    assert mock_bash.call_count == 7
    mock_hw.assert_called_once_with("/mnt", ["/dev/sda"], None)
    mock_run.assert_called_once_with(("nixos-install", "--root", "/mnt"), check=True)


def test_install_nixos_multiple_disks() -> None:
    """Test install_nixos formats all disk EFI partitions."""
    with (
        patch("python.installer.__main__.bash_wrapper") as mock_bash,
        patch("python.installer.__main__.run") as mock_run,
        patch("python.installer.__main__.create_nix_hardware_file") as mock_hw,
    ):
        install_nixos("/mnt", ["/dev/sda", "/dev/sdb"], encrypt="key")

    # 4 mount + 2 mkfs.vfat + 1 boot mount + 1 generate-config = 8
    assert mock_bash.call_count == 8
    # Check mkfs.vfat called for both disks
    bash_calls = [str(c) for c in mock_bash.call_args_list]
    assert any("mkfs.vfat" in c and "sda" in c for c in bash_calls)
    assert any("mkfs.vfat" in c and "sdb" in c for c in bash_calls)
    mock_hw.assert_called_once_with("/mnt", ["/dev/sda", "/dev/sdb"], "key")


def test_install_nixos_mounts_zfs_datasets() -> None:
    """Test install_nixos mounts all required ZFS datasets."""
    with (
        patch("python.installer.__main__.bash_wrapper") as mock_bash,
        patch("python.installer.__main__.run"),
        patch("python.installer.__main__.create_nix_hardware_file"),
    ):
        install_nixos("/mnt", ["/dev/sda"], encrypt=None)

    bash_calls = [str(c) for c in mock_bash.call_args_list]
    assert any("root_pool/root" in c for c in bash_calls)
    assert any("root_pool/home" in c for c in bash_calls)
    assert any("root_pool/var" in c for c in bash_calls)
    assert any("root_pool/nix" in c for c in bash_calls)


# --- installer (lines 244-280) ---


def test_installer_no_encrypt() -> None:
    """Test installer flow without encryption."""
    with (
        patch("python.installer.__main__.partition_disk") as mock_partition,
        patch("python.installer.__main__.Popen") as mock_popen,
        patch("python.installer.__main__.Path") as mock_path,
        patch("python.installer.__main__.create_zfs_pool") as mock_pool,
        patch("python.installer.__main__.create_zfs_datasets") as mock_datasets,
        patch("python.installer.__main__.install_nixos") as mock_install,
    ):
        installer(
            disks=("/dev/sda",),
            swap_size=8,
            reserve=0,
            encrypt_key=None,
        )

    mock_partition.assert_called_once_with("/dev/sda", 8, 0)
    mock_pool.assert_called_once_with(["/dev/sda-part2"], "/tmp/nix_install")
    mock_datasets.assert_called_once()
    mock_install.assert_called_once_with("/tmp/nix_install", ("/dev/sda",), None)


def test_installer_with_encrypt() -> None:
    """Test installer flow with encryption enabled."""
    with (
        patch("python.installer.__main__.partition_disk") as mock_partition,
        patch("python.installer.__main__.Popen") as mock_popen,
        patch("python.installer.__main__.sleep") as mock_sleep,
        patch("python.installer.__main__.run") as mock_run,
        patch("python.installer.__main__.Path") as mock_path,
        patch("python.installer.__main__.create_zfs_pool") as mock_pool,
        patch("python.installer.__main__.create_zfs_datasets") as mock_datasets,
        patch("python.installer.__main__.install_nixos") as mock_install,
    ):
        installer(
            disks=("/dev/sda",),
            swap_size=8,
            reserve=10,
            encrypt_key="secret",
        )

    mock_partition.assert_called_once_with("/dev/sda", 8, 10)
    mock_sleep.assert_called_once_with(1)
    # cryptsetup luksFormat and luksOpen
    assert mock_run.call_count == 2
    mock_pool.assert_called_once_with(
        ["/dev/mapper/luks-root-pool-sda-part2"],
        "/tmp/nix_install",
    )
    mock_datasets.assert_called_once()
    mock_install.assert_called_once_with("/tmp/nix_install", ("/dev/sda",), "secret")


def test_installer_multiple_disks_no_encrypt() -> None:
    """Test installer with multiple disks and no encryption."""
    with (
        patch("python.installer.__main__.partition_disk") as mock_partition,
        patch("python.installer.__main__.Popen") as mock_popen,
        patch("python.installer.__main__.Path") as mock_path,
        patch("python.installer.__main__.create_zfs_pool") as mock_pool,
        patch("python.installer.__main__.create_zfs_datasets") as mock_datasets,
        patch("python.installer.__main__.install_nixos") as mock_install,
    ):
        installer(
            disks=("/dev/sda", "/dev/sdb"),
            swap_size=4,
            reserve=0,
            encrypt_key=None,
        )

    assert mock_partition.call_count == 2
    mock_pool.assert_called_once_with(
        ["/dev/sda-part2", "/dev/sdb-part2"],
        "/tmp/nix_install",
    )


def test_installer_multiple_disks_with_encrypt() -> None:
    """Test installer with multiple disks and encryption."""
    with (
        patch("python.installer.__main__.partition_disk") as mock_partition,
        patch("python.installer.__main__.Popen") as mock_popen,
        patch("python.installer.__main__.sleep") as mock_sleep,
        patch("python.installer.__main__.run") as mock_run,
        patch("python.installer.__main__.Path") as mock_path,
        patch("python.installer.__main__.create_zfs_pool") as mock_pool,
        patch("python.installer.__main__.create_zfs_datasets") as mock_datasets,
        patch("python.installer.__main__.install_nixos") as mock_install,
    ):
        installer(
            disks=("/dev/sda", "/dev/sdb"),
            swap_size=4,
            reserve=2,
            encrypt_key="key123",
        )

    assert mock_partition.call_count == 2
    assert mock_sleep.call_count == 2
    # 2 disks x 2 cryptsetup commands = 4
    assert mock_run.call_count == 4
    mock_pool.assert_called_once_with(
        ["/dev/mapper/luks-root-pool-sda-part2", "/dev/mapper/luks-root-pool-sdb-part2"],
        "/tmp/nix_install",
    )


# --- main (lines 283-299) ---


def test_main_calls_installer() -> None:
    """Test main function orchestrates TUI and installer."""
    mock_state = MagicMock()
    mock_state.selected_device_ids = {"/dev/disk/by-id/ata-DISK1"}
    mock_state.get_selected_devices.return_value = ("/dev/disk/by-id/ata-DISK1",)
    mock_state.swap_size = 8
    mock_state.reserve_size = 0

    with (
        patch("python.installer.__main__.configure_logger"),
        patch("python.installer.__main__.curses.wrapper", return_value=mock_state),
        patch("python.installer.__main__.getenv", return_value=None),
        patch("python.installer.__main__.sleep"),
        patch("python.installer.__main__.installer") as mock_installer,
    ):
        main()

    mock_installer.assert_called_once_with(
        disks=("/dev/disk/by-id/ata-DISK1",),
        swap_size=8,
        reserve=0,
        encrypt_key=None,
    )


def test_main_with_encrypt_key() -> None:
    """Test main function passes encrypt key from environment."""
    mock_state = MagicMock()
    mock_state.selected_device_ids = {"/dev/disk/by-id/ata-DISK1"}
    mock_state.get_selected_devices.return_value = ("/dev/disk/by-id/ata-DISK1",)
    mock_state.swap_size = 16
    mock_state.reserve_size = 5

    with (
        patch("python.installer.__main__.configure_logger"),
        patch("python.installer.__main__.curses.wrapper", return_value=mock_state),
        patch("python.installer.__main__.getenv", return_value="my_encrypt_key"),
        patch("python.installer.__main__.sleep"),
        patch("python.installer.__main__.installer") as mock_installer,
    ):
        main()

    mock_installer.assert_called_once_with(
        disks=("/dev/disk/by-id/ata-DISK1",),
        swap_size=16,
        reserve=5,
        encrypt_key="my_encrypt_key",
    )


def test_main_calls_sleep() -> None:
    """Test main function sleeps for 3 seconds before installing."""
    mock_state = MagicMock()
    mock_state.selected_device_ids = set()
    mock_state.get_selected_devices.return_value = ()
    mock_state.swap_size = 0
    mock_state.reserve_size = 0

    with (
        patch("python.installer.__main__.configure_logger"),
        patch("python.installer.__main__.curses.wrapper", return_value=mock_state),
        patch("python.installer.__main__.getenv", return_value=None),
        patch("python.installer.__main__.sleep") as mock_sleep,
        patch("python.installer.__main__.installer"),
    ):
        main()

    mock_sleep.assert_called_once_with(3)
