"""test."""

from __future__ import annotations

import json
from typing import Any

from python.common import bash_wrapper


def _zpool_list(zfs_list: str) -> dict[str, Any]:
    """Check the version of zfs."""
    raw_zfs_list_data, _ = bash_wrapper(zfs_list)

    zfs_list_data = json.loads(raw_zfs_list_data)

    vers_major = zfs_list_data["output_version"]["vers_major"]
    vers_minor = zfs_list_data["output_version"]["vers_minor"]
    command = zfs_list_data["output_version"]["command"]

    if vers_major != 0 or vers_minor != 1 or command != "zpool list":
        error = f"Datasets are not in the correct format {vers_major=} {vers_minor=} {command=}"
        raise RuntimeError(error)

    return zfs_list_data


class Zpool:
    """Zpool."""

    def __init__(
        self,
        name: str,
    ) -> None:
        """__init__."""
        zpool_data = _zpool_list(f"zpool list {name} -pHj -o all")

        properties = zpool_data["pools"][name]["properties"]

        self.name = name

        self.allocated = int(properties["allocated"]["value"])
        self.altroot = properties["altroot"]["value"]
        self.ashift = int(properties["ashift"]["value"])
        self.autoexpand = properties["autoexpand"]["value"]
        self.autoreplace = properties["autoreplace"]["value"]
        self.autotrim = properties["autotrim"]["value"]
        self.capacity = int(properties["capacity"]["value"])
        self.comment = properties["comment"]["value"]
        self.dedupratio = properties["dedupratio"]["value"]
        self.delegation = properties["delegation"]["value"]
        self.expandsize = properties["expandsize"]["value"]
        self.failmode = properties["failmode"]["value"]
        self.fragmentation = int(properties["fragmentation"]["value"])
        self.free = properties["free"]["value"]
        self.freeing = int(properties["freeing"]["value"])
        self.guid = int(properties["guid"]["value"])
        self.health = properties["health"]["value"]
        self.leaked = int(properties["leaked"]["value"])
        self.readonly = properties["readonly"]["value"]
        self.size = int(properties["size"]["value"])

    def __repr__(self) -> str:
        """__repr__."""
        return (
            f"{self.name=}\n"
            f"{self.allocated=}\n"
            f"{self.altroot=}\n"
            f"{self.ashift=}\n"
            f"{self.autoexpand=}\n"
            f"{self.autoreplace=}\n"
            f"{self.autotrim=}\n"
            f"{self.capacity=}\n"
            f"{self.comment=}\n"
            f"{self.dedupratio=}\n"
            f"{self.delegation=}\n"
            f"{self.expandsize=}\n"
            f"{self.failmode=}\n"
            f"{self.fragmentation=}\n"
            f"{self.freeing=}\n"
            f"{self.guid=}\n"
            f"{self.health=}\n"
            f"{self.leaked=}\n"
            f"{self.readonly=}\n"
            f"{self.size=}"
        )
