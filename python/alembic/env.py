"""Alembic."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from alembic import context
from alembic.script import write_hooks

from python.common import bash_wrapper
from python.orm import RichieBase
from python.orm.base import get_postgres_engine

if TYPE_CHECKING:
    from collections.abc import MutableMapping

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


target_metadata = RichieBase.metadata
logging.basicConfig(
    level="DEBUG",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@write_hooks.register("dynamic_schema")
def dynamic_schema(filename: str, _options: dict[Any, Any]) -> None:
    """Dynamic schema."""
    original_file = Path(filename).read_text()
    dynamic_schema_file_part1 = original_file.replace(f"schema='{RichieBase.schema_name}'", "schema=schema")
    dynamic_schema_file = dynamic_schema_file_part1.replace(f"'{RichieBase.schema_name}.", "f'{schema}.")
    Path(filename).write_text(dynamic_schema_file)


@write_hooks.register("ruff")
def ruff_check_and_format(filename: str, _options: dict[Any, Any]) -> None:
    """Docstring for ruff_check_and_format."""
    bash_wrapper(f"ruff check --fix {filename}")
    bash_wrapper(f"ruff format {filename}")


def include_name(
    name: str | None,
    type_: Literal["schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint"],
    _parent_names: MutableMapping[Literal["schema_name", "table_name", "schema_qualified_table_name"], str | None],
) -> bool:
    """This filter table to be included in the migration.

    Args:
        name (str): The name of the table.
        type_ (str): The type of the table.
        parent_names (list[str]): The names of the parent tables.

    Returns:
        bool: True if the table should be included, False otherwise.

    """
    if type_ == "schema":
        return name == target_metadata.schema
    return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = get_postgres_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=RichieBase.schema_name,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
