from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def safe_insert(orm_objects: Sequence[object], session: Session) -> list[tuple[Exception, object]]:
    """Safer insert at allows for partial rollbacks.

    Args:
        orm_objects (Sequence[object]): Tables to insert.
        session (Session): Database session.
    """
    if unmapped := [orm_object for orm_object in orm_objects if not _is_mapped_instance(orm_object)]:
        error = f"binary_search_insert expects ORM-mapped instances {unmapped}"
        raise TypeError(error)
    return _safe_insert(orm_objects, session)


def _safe_insert(objects: Sequence[object], session: Session) -> list[tuple[Exception, object]]:
    exceptions: list[tuple[Exception, object]] = []
    try:
        session.add_all(objects)
        session.commit()

    except Exception as error:
        session.rollback()

        objects_len = len(objects)
        if objects_len == 1:
            logger.exception(objects)
            return [(error, objects[0])]

        middle = objects_len // 2
        exceptions.extend(_safe_insert(objects=objects[:middle], session=session))
        exceptions.extend(_safe_insert(objects=objects[middle:], session=session))
    return exceptions


def _is_mapped_instance(obj: object) -> bool:
    """Return True if `obj` is a SQLAlchemy ORM-mapped instance."""
    try:
        inspect(obj)  # raises NoInspectionAvailable if not mapped
    except NoInspectionAvailable:
        return False
    else:
        return True
