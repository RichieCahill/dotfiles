"""Validate Jeeves."""

from __future__ import annotations

import logging
from copy import copy
from re import search
from time import sleep
from typing import TYPE_CHECKING

from python.common import bash_wrapper
from python.zfs import Zpool

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


def zpool_tests(pool_names: Sequence[str], zpool_capacity_threshold: int = 90) -> list[str] | None:
    """Check the zpool health and capacity.

    Args:
        pool_names (Sequence[str]): A list of pool names to test.
        zpool_capacity_threshold (int, optional): The threshold for the zpool capacity. Defaults to 90.

    Returns:
        list[str] | None: A list of errors if any.
    """
    logger.info("Testing zpool")

    errors: list[str] = []
    for pool_name in pool_names:
        pool = Zpool(pool_name)
        if pool.health != "ONLINE":
            errors.append(f"{pool.name} is {pool.health}")
        if pool.capacity >= zpool_capacity_threshold:
            errors.append(f"{pool.name} is low on space")

    upgrade_status, _ = bash_wrapper("zpool upgrade")
    if not search(r"Every feature flags pool has all supported and requested features enabled.", upgrade_status):
        errors.append("ZPool out of date run `sudo zpool upgrade -a`")

    return errors


def systemd_tests(
    service_names: Sequence[str],
    max_retries: int = 30,
    retry_delay_secs: int = 1,
    retryable_statuses: Sequence[str] | None = None,
    valid_statuses: Sequence[str] | None = None,
) -> list[str] | None:
    """Tests a systemd services.

    Args:
        service_names (Sequence[str]): A list of service names to test.
        max_retries (int, optional): The maximum number of retries. Defaults to 30.
            minimum value is 1.
        retry_delay_secs (int, optional): The delay between retries in seconds. Defaults to 1.
            minimum value is 1.
        retryable_statuses (Sequence[str] | None, optional): A list of retryable statuses. Defaults to None.
        valid_statuses (Sequence[str] | None, optional): A list of valid statuses. Defaults to None.

    Returns:
        list[str] | None: A list of errors if any.
    """
    logger.info("Testing systemd service")

    max_retries = max(max_retries, 1)
    retry_delay_secs = max(retry_delay_secs, 1)
    last_try = max_retries - 1

    if retryable_statuses is None:
        retryable_statuses = ("inactive\n", "activating\n")

    if valid_statuses is None:
        valid_statuses = ("active\n",)

    service_names_set = set(service_names)

    errors: set[str] = set()
    for retry in range(max_retries):
        if not service_names_set:
            break
        logger.info(f"Testing systemd service in {retry + 1} of {max_retries}")
        service_names_to_test = copy(service_names_set)
        for service_name in service_names_to_test:
            service_status, _ = bash_wrapper(f"systemctl is-active {service_name}")
            if service_status in valid_statuses:
                service_names_set.remove(service_name)
                continue
            if service_status in retryable_statuses and retry < last_try:
                continue
            errors.add(f"{service_name} is {service_status.strip()}")

        sleep(retry_delay_secs)

    return list(errors)
