"""Extended tests for python/installer/__main__.py."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from python.installer.__main__ import (
    create_zfs_datasets,
    create_zfs_pool,
    get_boot_drive_id,
    partition_disk,
)


def test_create_zfs_datasets() -> None:
    """Test create_zfs_datasets creates expected datasets."""
    with patch("python.installer.__main__.bash_wrapper") as mock_bash:
        mock_bash.return_value = "NAME\nroot_pool\nroot_pool/root\nroot_pool/home\nroot_pool/var\nroot_pool/nix\n"
        create_zfs_datasets()
    assert mock_bash.call_count == 5  # 4 create + 1 list


def test_create_zfs_datasets_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_zfs_datasets exits on missing datasets."""
    with (
        patch("python.installer.__main__.bash_wrapper") as mock_bash,
        pytest.raises(SystemExit),
    ):
        mock_bash.return_value = "NAME\nroot_pool\n"
        create_zfs_datasets()


def test_create_zfs_pool_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_zfs_pool exits on failure."""
    with (
        patch("python.installer.__main__.bash_wrapper") as mock_bash,
        pytest.raises(SystemExit),
    ):
        mock_bash.return_value = "NAME\n"
        create_zfs_pool(["/dev/sda-part2"], "/mnt")


def test_get_boot_drive_id() -> None:
    """Test get_boot_drive_id extracts UUID."""
    with patch("python.installer.__main__.bash_wrapper", return_value="UUID\nABCD-1234\n"):
        result = get_boot_drive_id("/dev/sda")
    assert result == "ABCD-1234"
