"""snapshot_manager."""

from __future__ import annotations

import logging
import sys
import tomllib
from functools import cache
from pathlib import Path  # noqa: TC003 This is required for the typer CLI
from re import compile as re_compile
from re import search

import typer

from python.common import configure_logger, signal_alert, utcnow
from python.zfs import Dataset, get_datasets

logger = logging.getLogger(__name__)


def main(config_file: Path) -> None:
    """Main."""
    configure_logger(level="DEBUG")
    logger.info("Starting snapshot_manager")

    try:
        time_stamp = get_time_stamp()

        for dataset in get_datasets():
            status = dataset.create_snapshot(time_stamp)
            logger.debug(f"{status=}")
            if status != "snapshot created":
                msg = f"{dataset.name} failed to create snapshot {time_stamp}"
                logger.error(msg)
                signal_alert(msg)
                continue

            get_snapshots_to_delete(dataset, get_count_lookup(config_file, dataset.name))
    except Exception:
        logger.exception("snapshot_manager failed")
        signal_alert("snapshot_manager failed")
        sys.exit(1)
    else:
        logger.info("snapshot_manager completed")


def get_count_lookup(config_file: Path, dataset_name: str) -> dict[str, int]:
    """Get the count lookup.

    Args:
        config_file (Path): The path to the configuration file.
        dataset_name (str): The name of the dataset.

    Returns:
        dict[str, int]: The count lookup.
    """
    config_data = load_config_data(config_file)

    return config_data.get(dataset_name, get_default_config(config_data))


def get_default_config(config_data: dict[str, dict[str, int]]) -> dict[str, int]:
    """Get the default configuration.

    Args:
        config_data (dict[str, dict[str, int]]): The configuration data.

    Returns:
        dict[str, int]: The default configuration.
    """
    return config_data.get(
        "default",
        {"15_min": 4, "hourly": 12, "daily": 0, "monthly": 0},
    )


@cache
def load_config_data(config_file: Path) -> dict[str, dict[str, int]]:
    """Load a TOML configuration file.

    Args:
        config_file (Path): The path to the configuration file.

    Returns:
        dict: The configuration data.
    """
    return tomllib.loads(config_file.read_text())


def get_snapshots_to_delete(
    dataset: Dataset,
    count_lookup: dict[str, int],
) -> None:
    """Get snapshots to delete.

    Args:
        dataset (Dataset): the dataset
        count_lookup (dict[str, int]): the count lookup
    """
    snapshots = dataset.get_snapshots()

    if not snapshots:
        logger.info(f"{dataset.name} has no snapshots")
        return

    filters = (
        ("15_min", re_compile(r"auto_\d{10}(?:15|30|45)")),
        ("hourly", re_compile(r"auto_\d{8}(?!00)\d{2}00")),
        ("daily", re_compile(r"auto_\d{6}(?!01)\d{2}0000")),
        ("monthly", re_compile(r"auto_\d{6}010000")),
    )

    for filter_name, snapshot_filter in filters:
        logger.debug(f"{filter_name=}\n{snapshot_filter=}")

        filtered_snapshots = sorted(snapshot.name for snapshot in snapshots if search(snapshot_filter, snapshot.name))

        logger.debug(f"{filtered_snapshots=}")

        snapshots_wanted = count_lookup[filter_name]
        snapshots_being_deleted = filtered_snapshots[:-snapshots_wanted] if snapshots_wanted > 0 else filtered_snapshots

        logger.info(f"{snapshots_being_deleted} are being deleted")
        for snapshot in snapshots_being_deleted:
            if error := dataset.delete_snapshot(snapshot):
                error_message = f"{dataset.name}@{snapshot} failed to delete: {error}"
                signal_alert(error_message)
                logger.error(error_message)


def get_time_stamp() -> str:
    """Get the time stamp."""
    now = utcnow()
    nearest_15_min = now.replace(minute=(now.minute - (now.minute % 15)))
    return nearest_15_min.strftime("auto_%Y%m%d%H%M")


def cli() -> None:
    """CLI."""
    typer.run(main)


if __name__ == "__main__":
    cli()
