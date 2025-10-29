"""test_snapshot_manager."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from python.tools.snapshot_manager import get_snapshots_to_delete, get_time_stamp, load_config_data, main
from python.zfs.dataset import Dataset, Snapshot

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture

SNAPSHOT_MANAGER = "python.tools.snapshot_manager"


def patch_utcnow(mocker: MockerFixture, datetime_value: datetime) -> None:
    """patch_utcnow."""
    mocker.patch("python.tools.snapshot_manager.utcnow", return_value=datetime_value)


def create_mock_snapshot(mocker: MockerFixture, name: str) -> Snapshot:
    """create_mock_snapshot."""
    mock_snapshot = mocker.MagicMock(spec=Snapshot)
    mock_snapshot.name = name

    return mock_snapshot


def test_main(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """Test main."""
    load_config_data.cache_clear()

    mocker.patch(f"{SNAPSHOT_MANAGER}.get_time_stamp", return_value="2023-01-01T00:00:00")

    mock_dataset = mocker.MagicMock(spec=Dataset)
    mock_dataset.name = "test_dataset"
    mock_dataset.create_snapshot.return_value = "snapshot created"
    mock_get_datasets = mocker.patch(f"{SNAPSHOT_MANAGER}.get_datasets", return_value=(mock_dataset,))

    mock_get_snapshots_to_delete = mocker.patch(f"{SNAPSHOT_MANAGER}.get_snapshots_to_delete")
    mock_signal_alert = mocker.patch(f"{SNAPSHOT_MANAGER}.signal_alert")
    mock_snapshot_config_toml = '["default"]\n15_min = 8\nhourly = 24\ndaily = 0\nmonthly = 0\n'
    fs.create_file("/mock_snapshot_config.toml", contents=mock_snapshot_config_toml)
    main(Path("/mock_snapshot_config.toml"))

    mock_signal_alert.assert_not_called()
    mock_get_datasets.assert_called_once()
    mock_get_snapshots_to_delete.assert_called_once_with(
        mock_dataset,
        {
            "15_min": 8,
            "hourly": 24,
            "daily": 0,
            "monthly": 0,
        },
    )


def test_main_create_snapshot_failure(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """Test main."""
    load_config_data.cache_clear()

    mocker.patch(f"{SNAPSHOT_MANAGER}.get_time_stamp", return_value="2023-01-01T00:00:00")

    mock_dataset = mocker.MagicMock(spec=Dataset)
    mock_dataset.name = "test_dataset"
    mock_dataset.create_snapshot.return_value = "snapshot not created"
    mock_get_datasets = mocker.patch(f"{SNAPSHOT_MANAGER}.get_datasets", return_value=(mock_dataset,))

    mock_get_snapshots_to_delete = mocker.patch(f"{SNAPSHOT_MANAGER}.get_snapshots_to_delete")
    mock_signal_alert = mocker.patch(f"{SNAPSHOT_MANAGER}.signal_alert")
    mock_snapshot_config_toml = '["default"]\n15_min = 8\nhourly = 24\ndaily = 0\nmonthly = 0\n'
    fs.create_file("/mock_snapshot_config.toml", contents=mock_snapshot_config_toml)
    main(Path("/mock_snapshot_config.toml"))

    mock_signal_alert.assert_called_once_with("test_dataset failed to create snapshot 2023-01-01T00:00:00")
    mock_get_datasets.assert_called_once()
    mock_get_snapshots_to_delete.assert_not_called()


def test_main_exception(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """Test main."""
    load_config_data.cache_clear()

    mocker.patch(f"{SNAPSHOT_MANAGER}.get_time_stamp", return_value="2023-01-01T00:00:00")

    mock_dataset = mocker.MagicMock(spec=Dataset)
    mock_dataset.name = "test_dataset"
    mock_dataset.create_snapshot.return_value = "snapshot created"
    mock_get_datasets = mocker.patch(f"{SNAPSHOT_MANAGER}.get_datasets", side_effect=Exception("test"))

    mock_get_snapshots_to_delete = mocker.patch(f"{SNAPSHOT_MANAGER}.get_snapshots_to_delete")
    mock_signal_alert = mocker.patch(f"{SNAPSHOT_MANAGER}.signal_alert")
    mock_snapshot_config_toml = '["default"]\n15_min = 8\nhourly = 24\ndaily = 0\nmonthly = 0\n'
    fs.create_file("/mock_snapshot_config.toml", contents=mock_snapshot_config_toml)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main(Path("/mock_snapshot_config.toml"))

    assert isinstance(pytest_wrapped_e.value, SystemExit)
    assert pytest_wrapped_e.value.code == 1
    mock_signal_alert.assert_called_once_with("snapshot_manager failed")
    mock_get_datasets.assert_called_once()
    mock_get_snapshots_to_delete.assert_not_called()


def test_get_snapshots_to_delete(mocker: MockerFixture) -> None:
    """test_get_snapshots_to_delete."""
    mock_snapshot_0 = create_mock_snapshot(mocker, "auto_202509150415")
    mock_snapshot_1 = create_mock_snapshot(mocker, "auto_202509150415")

    mock_dataset = mocker.MagicMock(spec=Dataset)
    mock_dataset.name = "test_dataset"
    mock_dataset.get_snapshots.return_value = (mock_snapshot_0, mock_snapshot_1)
    mock_dataset.delete_snapshot.return_value = None

    mock_signal_alert = mocker.patch(f"{SNAPSHOT_MANAGER}.signal_alert")

    get_snapshots_to_delete(mock_dataset, {"15_min": 1, "hourly": 0, "daily": 0, "monthly": 0})

    mock_signal_alert.assert_not_called()
    mock_dataset.delete_snapshot.assert_called_once_with("auto_202509150415")


def test_get_snapshots_to_delete_no_snapshot(mocker: MockerFixture) -> None:
    """test_get_snapshots_to_delete_no_snapshot."""
    mock_dataset = mocker.MagicMock(spec=Dataset)
    mock_dataset.name = "test_dataset"
    mock_dataset.get_snapshots.return_value = ()
    mock_dataset.delete_snapshot.return_value = None

    mock_signal_alert = mocker.patch(f"{SNAPSHOT_MANAGER}.signal_alert")

    get_snapshots_to_delete(mock_dataset, {"15_min": 1, "hourly": 0, "daily": 0, "monthly": 0})

    mock_signal_alert.assert_not_called()
    mock_dataset.delete_snapshot.assert_not_called()


def test_get_snapshots_to_delete_errored(mocker: MockerFixture) -> None:
    """test_get_snapshots_to_delete_errored."""
    mock_snapshot_0 = create_mock_snapshot(mocker, "auto_202509150415")
    mock_snapshot_1 = create_mock_snapshot(mocker, "auto_202509150415")

    mock_dataset = mocker.MagicMock(spec=Dataset)
    mock_dataset.name = "test_dataset"
    mock_dataset.get_snapshots.return_value = (mock_snapshot_0, mock_snapshot_1)
    mock_dataset.delete_snapshot.return_value = "snapshot has dependent clones"

    mock_signal_alert = mocker.patch(f"{SNAPSHOT_MANAGER}.signal_alert")

    get_snapshots_to_delete(mock_dataset, {"15_min": 1, "hourly": 0, "daily": 0, "monthly": 0})

    mock_signal_alert.assert_called_once_with(
        "test_dataset@auto_202509150415 failed to delete: snapshot has dependent clones"
    )
    mock_dataset.delete_snapshot.assert_called_once_with("auto_202509150415")


def test_get_time_stamp(mocker: MockerFixture) -> None:
    """Test get_time_stamp."""
    patch_utcnow(mocker, datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC))
    assert get_time_stamp() == "auto_202301010000"
