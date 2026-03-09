"""Tests for python/zfs/dataset.py covering missing lines."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from python.zfs.dataset import Dataset, Snapshot, _zfs_list

DATASET = "python.zfs.dataset"

SAMPLE_SNAPSHOT_DATA = {
    "createtxg": "123",
    "properties": {
        "creation": {"value": "1620000000"},
        "defer_destroy": {"value": "off"},
        "guid": {"value": "456"},
        "objsetid": {"value": "789"},
        "referenced": {"value": "1024"},
        "used": {"value": "512"},
        "userrefs": {"value": "0"},
        "version": {"value": "1"},
        "written": {"value": "2048"},
    },
    "name": "pool/dataset@snap1",
}

SAMPLE_DATASET_DATA = {
    "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zfs list"},
    "datasets": {
        "pool/dataset": {
            "properties": {
                "aclinherit": {"value": "restricted"},
                "aclmode": {"value": "discard"},
                "acltype": {"value": "off"},
                "available": {"value": "1000000"},
                "canmount": {"value": "on"},
                "checksum": {"value": "on"},
                "clones": {"value": ""},
                "compression": {"value": "lz4"},
                "copies": {"value": "1"},
                "createtxg": {"value": "1234"},
                "creation": {"value": "1620000000"},
                "dedup": {"value": "off"},
                "devices": {"value": "on"},
                "encryption": {"value": "off"},
                "exec": {"value": "on"},
                "filesystem_limit": {"value": "none"},
                "guid": {"value": "5678"},
                "keystatus": {"value": "none"},
                "logbias": {"value": "latency"},
                "mlslabel": {"value": "none"},
                "mounted": {"value": "yes"},
                "mountpoint": {"value": "/pool/dataset"},
                "quota": {"value": "0"},
                "readonly": {"value": "off"},
                "recordsize": {"value": "131072"},
                "redundant_metadata": {"value": "all"},
                "referenced": {"value": "512000"},
                "refquota": {"value": "0"},
                "refreservation": {"value": "0"},
                "reservation": {"value": "0"},
                "setuid": {"value": "on"},
                "sharenfs": {"value": "off"},
                "snapdir": {"value": "hidden"},
                "snapshot_limit": {"value": "none"},
                "sync": {"value": "standard"},
                "used": {"value": "1024000"},
                "usedbychildren": {"value": "512000"},
                "usedbydataset": {"value": "256000"},
                "usedbysnapshots": {"value": "256000"},
                "version": {"value": "5"},
                "volmode": {"value": "default"},
                "volsize": {"value": "none"},
                "vscan": {"value": "off"},
                "written": {"value": "4096"},
                "xattr": {"value": "on"},
            }
        }
    },
}


def _make_dataset() -> Dataset:
    """Create a Dataset instance with mocked _zfs_list."""
    with patch(f"{DATASET}._zfs_list", return_value=SAMPLE_DATASET_DATA):
        return Dataset("pool/dataset")


# --- _zfs_list version check error (line 29) ---


def test_zfs_list_returns_data_on_valid_version() -> None:
    """Test _zfs_list returns parsed data when version is correct."""
    valid_data = {
        "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zfs list"},
        "datasets": {},
    }
    with patch(f"{DATASET}.bash_wrapper", return_value=(json.dumps(valid_data), 0)):
        result = _zfs_list("zfs list pool -pHj -o all")
    assert result == valid_data


def test_zfs_list_raises_on_wrong_vers_minor() -> None:
    """Test _zfs_list raises RuntimeError when vers_minor is wrong."""
    bad_data = {
        "output_version": {"vers_major": 0, "vers_minor": 2, "command": "zfs list"},
    }
    with (
        patch(f"{DATASET}.bash_wrapper", return_value=(json.dumps(bad_data), 0)),
        pytest.raises(RuntimeError, match="Datasets are not in the correct format"),
    ):
        _zfs_list("zfs list pool -pHj -o all")


def test_zfs_list_raises_on_wrong_command() -> None:
    """Test _zfs_list raises RuntimeError when command field is wrong."""
    bad_data = {
        "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zpool list"},
    }
    with (
        patch(f"{DATASET}.bash_wrapper", return_value=(json.dumps(bad_data), 0)),
        pytest.raises(RuntimeError, match="Datasets are not in the correct format"),
    ):
        _zfs_list("zfs list pool -pHj -o all")


# --- Snapshot.__repr__() (line 52) ---


def test_snapshot_repr() -> None:
    """Test Snapshot __repr__ returns correct format."""
    snapshot = Snapshot(SAMPLE_SNAPSHOT_DATA)
    result = repr(snapshot)
    assert result == "name=snap1 used=512 refer=1024"


def test_snapshot_repr_different_values() -> None:
    """Test Snapshot __repr__ with different values."""
    data = {
        **SAMPLE_SNAPSHOT_DATA,
        "name": "pool/dataset@daily-2024-01-01",
        "properties": {
            **SAMPLE_SNAPSHOT_DATA["properties"],
            "used": {"value": "999"},
            "referenced": {"value": "5555"},
        },
    }
    snapshot = Snapshot(data)
    assert "daily-2024-01-01" in repr(snapshot)
    assert "999" in repr(snapshot)
    assert "5555" in repr(snapshot)


# --- Dataset.get_snapshots() (lines 113-115) ---


def test_dataset_get_snapshots() -> None:
    """Test Dataset.get_snapshots returns list of Snapshot objects."""
    dataset = _make_dataset()

    snapshot_list_data = {
        "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zfs list"},
        "datasets": {
            "pool/dataset@snap1": SAMPLE_SNAPSHOT_DATA,
            "pool/dataset@snap2": {
                **SAMPLE_SNAPSHOT_DATA,
                "name": "pool/dataset@snap2",
            },
        },
    }
    with patch(f"{DATASET}._zfs_list", return_value=snapshot_list_data):
        snapshots = dataset.get_snapshots()

    assert snapshots is not None
    assert len(snapshots) == 2
    assert all(isinstance(s, Snapshot) for s in snapshots)


def test_dataset_get_snapshots_empty() -> None:
    """Test Dataset.get_snapshots returns empty list when no snapshots."""
    dataset = _make_dataset()

    snapshot_list_data = {
        "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zfs list"},
        "datasets": {},
    }
    with patch(f"{DATASET}._zfs_list", return_value=snapshot_list_data):
        snapshots = dataset.get_snapshots()

    assert snapshots == []


# --- Dataset.create_snapshot() (lines 123-133) ---


def test_dataset_create_snapshot_success() -> None:
    """Test create_snapshot returns success message when return code is 0."""
    dataset = _make_dataset()

    with patch(f"{DATASET}.bash_wrapper", return_value=("", 0)):
        result = dataset.create_snapshot("my-snap")

    assert result == "snapshot created"


def test_dataset_create_snapshot_already_exists() -> None:
    """Test create_snapshot returns message when snapshot already exists."""
    dataset = _make_dataset()

    snapshot_list_data = {
        "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zfs list"},
        "datasets": {
            "pool/dataset@my-snap": SAMPLE_SNAPSHOT_DATA,
        },
    }

    with (
        patch(f"{DATASET}.bash_wrapper", return_value=("dataset already exists", 1)),
        patch(f"{DATASET}._zfs_list", return_value=snapshot_list_data),
    ):
        # The snapshot data has name "pool/dataset@snap1" which extracts to "snap1"
        # We need the snapshot name to match, so use "snap1"
        result = dataset.create_snapshot("snap1")

    assert "already exists" in result


def test_dataset_create_snapshot_failure() -> None:
    """Test create_snapshot returns failure message on unknown error."""
    dataset = _make_dataset()

    snapshot_list_data = {
        "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zfs list"},
        "datasets": {},
    }

    with (
        patch(f"{DATASET}.bash_wrapper", return_value=("some error", 1)),
        patch(f"{DATASET}._zfs_list", return_value=snapshot_list_data),
    ):
        result = dataset.create_snapshot("new-snap")

    assert "Failed to create snapshot" in result


def test_dataset_create_snapshot_failure_no_snapshots() -> None:
    """Test create_snapshot failure when get_snapshots returns empty list."""
    dataset = _make_dataset()

    # get_snapshots returns empty list (falsy), so the if branch is skipped
    snapshot_list_data = {
        "output_version": {"vers_major": 0, "vers_minor": 1, "command": "zfs list"},
        "datasets": {},
    }

    with (
        patch(f"{DATASET}.bash_wrapper", return_value=("error", 1)),
        patch(f"{DATASET}._zfs_list", return_value=snapshot_list_data),
    ):
        result = dataset.create_snapshot("nonexistent")

    assert "Failed to create snapshot" in result


# --- Dataset.delete_snapshot() (lines 141-148) ---


def test_dataset_delete_snapshot_success() -> None:
    """Test delete_snapshot returns None on success."""
    dataset = _make_dataset()

    with patch(f"{DATASET}.bash_wrapper", return_value=("", 0)):
        result = dataset.delete_snapshot("my-snap")

    assert result is None


def test_dataset_delete_snapshot_dependent_clones() -> None:
    """Test delete_snapshot returns message when snapshot has dependent clones."""
    dataset = _make_dataset()

    error_msg = "cannot destroy 'pool/dataset@my-snap': snapshot has dependent clones"
    with patch(f"{DATASET}.bash_wrapper", return_value=(error_msg, 1)):
        result = dataset.delete_snapshot("my-snap")

    assert result == "snapshot has dependent clones"


def test_dataset_delete_snapshot_other_failure() -> None:
    """Test delete_snapshot raises RuntimeError on other failures."""
    dataset = _make_dataset()

    with (
        patch(f"{DATASET}.bash_wrapper", return_value=("some other error", 1)),
        pytest.raises(RuntimeError, match="Failed to delete snapshot"),
    ):
        dataset.delete_snapshot("my-snap")


# --- Dataset.__repr__() (line 152) ---


def test_dataset_repr() -> None:
    """Test Dataset __repr__ includes all attributes."""
    dataset = _make_dataset()
    result = repr(dataset)

    expected_attrs = [
        "aclinherit",
        "aclmode",
        "acltype",
        "available",
        "canmount",
        "checksum",
        "clones",
        "compression",
        "copies",
        "createtxg",
        "creation",
        "dedup",
        "devices",
        "encryption",
        "exec",
        "filesystem_limit",
        "guid",
        "keystatus",
        "logbias",
        "mlslabel",
        "mounted",
        "mountpoint",
        "name",
        "quota",
        "readonly",
        "recordsize",
        "redundant_metadata",
        "referenced",
        "refquota",
        "refreservation",
        "reservation",
        "setuid",
        "sharenfs",
        "snapdir",
        "snapshot_limit",
        "sync",
        "used",
        "usedbychildren",
        "usedbydataset",
        "usedbysnapshots",
        "version",
        "volmode",
        "volsize",
        "vscan",
        "written",
        "xattr",
    ]

    for attr in expected_attrs:
        assert f"self.{attr}=" in result, f"Missing {attr} in repr"
