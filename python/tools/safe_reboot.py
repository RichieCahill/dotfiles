"""Safe reboot helper."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from python.common import bash_wrapper, configure_logger
from python.zfs import Dataset, get_datasets

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


def get_root_pool_datasets(dataset_prefix: str) -> list[Dataset]:
    """Return datasets that start with the provided prefix."""
    return [dataset for dataset in get_datasets() if dataset.name.startswith(dataset_prefix)]


def get_non_executable_datasets(datasets: Sequence[Dataset]) -> list[str]:
    """Return dataset names that have exec disabled."""
    return [dataset.name for dataset in datasets if dataset.exec.lower() != "on"]


def drive_present(drive: str) -> bool:
    """Check whether the provided drive exists."""
    drive_path = drive.strip()
    if not drive_path:
        error = "Drive path cannot be empty"
        raise ValueError(error)

    return Path(drive_path).exists()


def reboot_system() -> None:
    """Call systemctl reboot."""
    output, return_code = bash_wrapper("systemctl reboot")
    if return_code != 0:
        raise RuntimeError(output.strip() or "Failed to issue reboot command")


def validate_state(drive: str | None, dataset_prefix: str) -> list[str]:
    """Validate dataset and drive state."""
    datasets = get_root_pool_datasets(dataset_prefix)

    errors: list[str] = []
    if not datasets:
        errors.append(f"No datasets found with prefix {dataset_prefix}")
    else:
        non_exec_datasets = get_non_executable_datasets(datasets)
        if non_exec_datasets:
            errors.append(f"Datasets missing exec=on: {', '.join(non_exec_datasets)}")

    if drive:
        try:
            if not drive_present(drive):
                errors.append(f"Drive {drive} is not present")
        except ValueError as err:
            errors.append(str(err))

    return errors


def reboot(
    drive: Annotated[str | None, typer.Argument(help="Drive that must exist before rebooting.")] = None,
    dataset_prefix: Annotated[
        str,
        typer.Option(
            "--dataset-prefix",
            "-p",
            help="Datasets with this prefix are validated.",
        ),
    ] = "root_pool/",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--check-only",
            help="Only validate state without issuing the reboot command.",
        ),
    ] = False,
) -> None:
    """Validate datasets and drive before rebooting."""
    configure_logger()
    logger.info("Starting safe reboot checks")

    if errors := validate_state(drive, dataset_prefix):
        for error in errors:
            logger.error(error)
        sys.exit(1)

    if dry_run:
        logger.info("All checks passed")
        return

    logger.info("All checks passed, issuing reboot")
    reboot_system()


def cli() -> None:
    """CLI entry point."""
    typer.run(reboot)


if __name__ == "__main__":
    cli()
