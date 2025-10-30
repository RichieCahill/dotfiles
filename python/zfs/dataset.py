"""dataset."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from python.common import bash_wrapper

logger = logging.getLogger(__name__)


def _zfs_list(zfs_list: str) -> dict[str, Any]:
    """Check the version of zfs."""
    raw_zfs_list_data, _ = bash_wrapper(zfs_list)

    zfs_list_data = json.loads(raw_zfs_list_data)

    vers_major = zfs_list_data["output_version"]["vers_major"]
    vers_minor = zfs_list_data["output_version"]["vers_minor"]
    command = zfs_list_data["output_version"]["command"]

    if vers_major != 0 or vers_minor != 1 or command != "zfs list":
        error = f"Datasets are not in the correct format {vers_major=} {vers_minor=} {command=}"
        raise RuntimeError(error)

    return zfs_list_data


class Snapshot:
    """Snapshot."""

    def __init__(self, snapshot_data: dict[str, Any]) -> None:
        """__init__."""
        properties = snapshot_data["properties"]
        self.createtxg = int(snapshot_data["createtxg"])
        self.creation = datetime.fromtimestamp(int(properties["creation"]["value"]), tz=UTC)
        self.defer_destroy = properties["defer_destroy"]["value"]
        self.guid = int(properties["guid"]["value"])
        self.name = snapshot_data["name"].split("@")[1]
        self.objsetid = int(properties["objsetid"]["value"])
        self.referenced = int(properties["referenced"]["value"])
        self.used = int(properties["used"]["value"])
        self.userrefs = int(properties["userrefs"]["value"])
        self.version = int(properties["version"]["value"])
        self.written = int(properties["written"]["value"])

    def __repr__(self) -> str:
        """__repr__."""
        return f"name={self.name} used={self.used} refer={self.referenced}"


class Dataset:
    """Dataset."""

    def __init__(self, name: str) -> None:
        """__init__."""
        dataset_data = _zfs_list(f"zfs list {name} -pHj -o all")

        properties = dataset_data["datasets"][name]["properties"]

        self.aclinherit = properties["aclinherit"]["value"]
        self.aclmode = properties["aclmode"]["value"]
        self.acltype = properties["acltype"]["value"]
        self.available = int(properties["available"]["value"])
        self.canmount = properties["canmount"]["value"]
        self.checksum = properties["checksum"]["value"]
        self.clones = properties["clones"]["value"]
        self.compression = properties["compression"]["value"]
        self.copies = int(properties["copies"]["value"])
        self.createtxg = int(properties["createtxg"]["value"])
        self.creation = datetime.fromtimestamp(int(properties["creation"]["value"]), tz=UTC)
        self.dedup = properties["dedup"]["value"]
        self.devices = properties["devices"]["value"]
        self.encryption = properties["encryption"]["value"]
        self.exec = properties["exec"]["value"]
        self.filesystem_limit = properties["filesystem_limit"]["value"]
        self.guid = int(properties["guid"]["value"])
        self.keystatus = properties["keystatus"]["value"]
        self.logbias = properties["logbias"]["value"]
        self.mlslabel = properties["mlslabel"]["value"]
        self.mounted = properties["mounted"]["value"]
        self.mountpoint = properties["mountpoint"]["value"]
        self.name = name
        self.quota = int(properties["quota"]["value"])
        self.readonly = properties["readonly"]["value"]
        self.recordsize = int(properties["recordsize"]["value"])
        self.redundant_metadata = properties["redundant_metadata"]["value"]
        self.referenced = int(properties["referenced"]["value"])
        self.refquota = int(properties["refquota"]["value"])
        self.refreservation = int(properties["refreservation"]["value"])
        self.reservation = int(properties["reservation"]["value"])
        self.setuid = properties["setuid"]["value"]
        self.sharenfs = properties["sharenfs"]["value"]
        self.snapdir = properties["snapdir"]["value"]
        self.snapshot_limit = properties["snapshot_limit"]["value"]
        self.sync = properties["sync"]["value"]
        self.used = int(properties["used"]["value"])
        self.usedbychildren = int(properties["usedbychildren"]["value"])
        self.usedbydataset = int(properties["usedbydataset"]["value"])
        self.usedbysnapshots = int(properties["usedbysnapshots"]["value"])
        self.version = int(properties["version"]["value"])
        self.volmode = properties["volmode"]["value"]
        self.volsize = properties["volsize"]["value"]
        self.vscan = properties["vscan"]["value"]
        self.written = int(properties["written"]["value"])
        self.xattr = properties["xattr"]["value"]

    def get_snapshots(self) -> list[Snapshot] | None:
        """Get all snapshots from zfs and process then is test dicts of sets."""
        snapshots_data = _zfs_list(f"zfs list -t snapshot -pHj {self.name} -o all")

        return [Snapshot(properties) for properties in snapshots_data["datasets"].values()]

    def create_snapshot(self, snapshot_name: str) -> str:
        """Creates a zfs snapshot.

        Args:
            snapshot_name (str): a snapshot name
        """
        logger.debug(f"Creating {self.name}@{snapshot_name}")
        _, return_code = bash_wrapper(f"zfs snapshot {self.name}@{snapshot_name}")
        if return_code == 0:
            return "snapshot created"

        if snapshots := self.get_snapshots():
            snapshot_names = {snapshot.name for snapshot in snapshots}
            if snapshot_name in snapshot_names:
                return f"Snapshot {snapshot_name} already exists for {self.name}"

        return f"Failed to create snapshot {snapshot_name} for {self.name}"

    def delete_snapshot(self, snapshot_name: str) -> str | None:
        """Deletes a zfs snapshot.

        Args:
            snapshot_name (str): a snapshot name
        """
        logger.debug(f"deleting {self.name}@{snapshot_name}")
        msg, return_code = bash_wrapper(f"zfs destroy {self.name}@{snapshot_name}")
        if return_code != 0:
            if msg.startswith(f"cannot destroy '{self.name}@{snapshot_name}': snapshot has dependent clones"):
                return "snapshot has dependent clones"
            error = f"Failed to delete snapshot {snapshot_name=} for {self.name}"
            raise RuntimeError(error)
        return None

    def __repr__(self) -> str:
        """__repr__."""
        return (
            f"{self.aclinherit=}\n"
            f"{self.aclmode=}\n"
            f"{self.acltype=}\n"
            f"{self.available=}\n"
            f"{self.canmount=}\n"
            f"{self.checksum=}\n"
            f"{self.clones=}\n"
            f"{self.compression=}\n"
            f"{self.copies=}\n"
            f"{self.createtxg=}\n"
            f"{self.creation=}\n"
            f"{self.dedup=}\n"
            f"{self.devices=}\n"
            f"{self.encryption=}\n"
            f"{self.exec=}\n"
            f"{self.filesystem_limit=}\n"
            f"{self.guid=}\n"
            f"{self.keystatus=}\n"
            f"{self.logbias=}\n"
            f"{self.mlslabel=}\n"
            f"{self.mounted=}\n"
            f"{self.mountpoint=}\n"
            f"{self.name=}\n"
            f"{self.quota=}\n"
            f"{self.readonly=}\n"
            f"{self.recordsize=}\n"
            f"{self.redundant_metadata=}\n"
            f"{self.referenced=}\n"
            f"{self.refquota=}\n"
            f"{self.refreservation=}\n"
            f"{self.reservation=}\n"
            f"{self.setuid=}\n"
            f"{self.sharenfs=}\n"
            f"{self.snapdir=}\n"
            f"{self.snapshot_limit=}\n"
            f"{self.sync=}\n"
            f"{self.used=}\n"
            f"{self.usedbychildren=}\n"
            f"{self.usedbydataset=}\n"
            f"{self.usedbysnapshots=}\n"
            f"{self.version=}\n"
            f"{self.volmode=}\n"
            f"{self.volsize=}\n"
            f"{self.vscan=}\n"
            f"{self.written=}\n"
            f"{self.xattr=}\n"
        )


def get_datasets() -> list[Dataset]:
    """Get zfs list.

    Returns:
        list[Dataset]: A list of zfs datasets.
    """
    logger.info("Getting zfs list")

    dataset_names, _ = bash_wrapper("zfs list -Hp -t filesystem -o name")

    cleaned_datasets = dataset_names.strip().split("\n")

    return [Dataset(dataset_name) for dataset_name in cleaned_datasets if "/" in dataset_name]
