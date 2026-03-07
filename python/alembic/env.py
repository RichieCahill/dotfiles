"""Alembic."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from alembic import context
from alembic.script import write_hooks
from sqlalchemy.schema import CreateSchema

from python.common import bash_wrapper
from python.orm.common import get_postgres_engine

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from sqlalchemy.orm import DeclarativeBase

config = context.config

base_class: type[DeclarativeBase] = config.attributes.get("base")
if base_class is None:
    error = "No base class provided. Use the database CLI to run alembic commands."
    raise RuntimeError(error)

target_metadata = base_class.metadata
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
    schema_name = base_class.schema_name
    dynamic_schema_file_part1 = original_file.replace(f"schema='{schema_name}'", "schema=schema")
    dynamic_schema_file = dynamic_schema_file_part1.replace(f"'{schema_name}.", "f'{schema}.")
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
    """Filter tables to be included in the migration.

    Args:
        name (str): The name of the table.
        type_ (str): The type of the table.
        _parent_names (MutableMapping): The names of the parent tables.

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
    env_prefix = config.attributes.get("env_prefix", "POSTGRES")
    connectable = get_postgres_engine(name=env_prefix)

    with connectable.connect() as connection:
        schema = base_class.schema_name
        if not connectable.dialect.has_schema(connection, schema):
            answer = input(f"Schema {schema!r} does not exist. Create it? [y/N] ")
            if answer.lower() != "y":
                error = f"Schema {schema!r} does not exist. Exiting."
                raise SystemExit(error)
            connection.execute(CreateSchema(schema))
            connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=schema,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
