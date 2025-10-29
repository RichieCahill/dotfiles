"""test_server_validate_scripts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pytest_mock import MockerFixture

from python.system_tests.validate_system import main

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture

VALIDATE_SYSTEM = "python.system_tests.validate_system"


def test_validate_system(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """test_validate_system."""
    fs.create_file(
        "/mock_snapshot_config.toml",
        contents='zpool = ["root_pool", "storage", "media"]\nservices = ["docker"]\n',
    )

    mocker.patch(f"{VALIDATE_SYSTEM}.systemd_tests", return_value=None)
    mocker.patch(f"{VALIDATE_SYSTEM}.zpool_tests", return_value=None)
    main(Path("/mock_snapshot_config.toml"))


def test_validate_system_errors(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """test_validate_system_errors."""
    fs.create_file(
        "/mock_snapshot_config.toml",
        contents='zpool = ["root_pool", "storage", "media"]\nservices = ["docker"]\n',
    )

    mocker.patch(f"{VALIDATE_SYSTEM}.systemd_tests", return_value=["systemd_tests error"])
    mocker.patch(f"{VALIDATE_SYSTEM}.zpool_tests", return_value=["zpool_tests error"])

    with pytest.raises(SystemExit) as exception_info:
        main(Path("/mock_snapshot_config.toml"))

    assert exception_info.value.code == 1


def test_validate_system_execution(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """test_validate_system_execution."""
    fs.create_file(
        "/mock_snapshot_config.toml",
        contents='zpool = ["root_pool", "storage", "media"]\nservices = ["docker"]\n',
    )

    mocker.patch(f"{VALIDATE_SYSTEM}.zpool_tests", side_effect=RuntimeError("zpool_tests error"))

    with pytest.raises(SystemExit) as exception_info:
        main(Path("/mock_snapshot_config.toml"))

    assert exception_info.value.code == 1
