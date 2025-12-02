"""Tests for safe_reboot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from python.tools.safe_reboot import reboot
from python.zfs.dataset import Dataset

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

SAFE_REBOOT = "python.tools.safe_reboot"


def create_dataset(mocker: MockerFixture, name: str, exec_state: str) -> Dataset:
    """Create a mock dataset."""
    dataset = mocker.MagicMock(spec=Dataset)
    dataset.name = name
    dataset.exec = exec_state
    return dataset


def test_reboot_reboots_when_checks_pass(mocker: MockerFixture) -> None:
    """The command should reboot when all checks pass."""
    dataset = create_dataset(mocker, "root_pool/root", "on")
    mocker.patch(f"{SAFE_REBOOT}.get_datasets", return_value=(dataset,))
    mocker.patch(f"{SAFE_REBOOT}.drive_present", return_value=True)
    mock_bash = mocker.patch(f"{SAFE_REBOOT}.bash_wrapper", return_value=("", 0))

    reboot("/dev/disk/root-drive")

    mock_bash.assert_called_once_with("systemctl reboot")


def test_reboot_reboots_without_drive_requirement(mocker: MockerFixture) -> None:
    """The command should reboot even when no drive is provided."""
    dataset = create_dataset(mocker, "root_pool/root", "on")
    mocker.patch(f"{SAFE_REBOOT}.get_datasets", return_value=(dataset,))
    mock_bash = mocker.patch(f"{SAFE_REBOOT}.bash_wrapper", return_value=("", 0))

    reboot(None)

    mock_bash.assert_called_once_with("systemctl reboot")


def test_reboot_errors_on_non_exec_dataset(mocker: MockerFixture) -> None:
    """The command should exit when a dataset lacks exec."""
    dataset = create_dataset(mocker, "root_pool/root", "off")
    mocker.patch(f"{SAFE_REBOOT}.get_datasets", return_value=(dataset,))
    mocker.patch(f"{SAFE_REBOOT}.drive_present", return_value=True)
    mocker.patch(f"{SAFE_REBOOT}.bash_wrapper", return_value=("", 0))

    with pytest.raises(SystemExit) as excinfo:
        reboot("/dev/disk/root-drive")

    assert excinfo.value.code == 1


def test_reboot_errors_when_driver_missing(mocker: MockerFixture) -> None:
    """The command should exit when the requested driver is absent."""
    dataset = create_dataset(mocker, "root_pool/root", "on")
    mocker.patch(f"{SAFE_REBOOT}.get_datasets", return_value=(dataset,))
    mocker.patch(f"{SAFE_REBOOT}.drive_present", return_value=False)
    mocker.patch(f"{SAFE_REBOOT}.bash_wrapper", return_value=("", 0))

    with pytest.raises(SystemExit) as excinfo:
        reboot("/dev/disk/root-drive")

    assert excinfo.value.code == 1


def test_reboot_errors_when_no_datasets_found(mocker: MockerFixture) -> None:
    """The command should exit when no datasets match the prefix."""
    mocker.patch(f"{SAFE_REBOOT}.get_datasets", return_value=())
    mocker.patch(f"{SAFE_REBOOT}.drive_present", return_value=True)
    mocker.patch(f"{SAFE_REBOOT}.bash_wrapper", return_value=("", 0))

    with pytest.raises(SystemExit) as excinfo:
        reboot("/dev/disk/root-drive")

    assert excinfo.value.code == 1


def test_reboot_check_only_skips_reboot(mocker: MockerFixture) -> None:
    """The command should only validate when --check-only is provided."""
    dataset = create_dataset(mocker, "root_pool/root", "on")
    mocker.patch(f"{SAFE_REBOOT}.get_datasets", return_value=(dataset,))
    mocker.patch(f"{SAFE_REBOOT}.drive_present", return_value=True)
    mock_bash = mocker.patch(f"{SAFE_REBOOT}.bash_wrapper", return_value=("", 0))

    reboot("/dev/disk/root-drive", check_only=True)

    mock_bash.assert_not_called()
