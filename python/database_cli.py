"""CLI wrapper around alembic for multi-database support.

Usage:
    database <db_name> <command> [args...]

Examples:
    database van_inventory upgrade head
    database van_inventory downgrade head-1
    database van_inventory revision --autogenerate -m "add meals table"
    database van_inventory check
    database richie check
    database richie upgrade head
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Annotated

import typer
from alembic.config import CommandLine, Config

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for a database."""

    env_prefix: str
    version_location: str
    base_module: str
    base_class_name: str
    models_module: str
    script_location: str = "python/alembic"
    file_template: str = "%%(year)d_%%(month).2d_%%(day).2d-%%(slug)s_%%(rev)s"

    def get_base(self) -> type[DeclarativeBase]:
        """Import and return the Base class."""
        module = import_module(self.base_module)
        return getattr(module, self.base_class_name)

    def import_models(self) -> None:
        """Import ORM models so alembic autogenerate can detect them."""
        import_module(self.models_module)

    def alembic_config(self) -> Config:
        """Build an alembic Config for this database."""
        # Runtime import needed — Config is in TYPE_CHECKING for the return type annotation
        from alembic.config import Config as AlembicConfig  # noqa: PLC0415

        cfg = AlembicConfig()
        cfg.set_main_option("script_location", self.script_location)
        cfg.set_main_option("file_template", self.file_template)
        cfg.set_main_option("prepend_sys_path", ".")
        cfg.set_main_option("version_path_separator", "os")
        cfg.set_main_option("version_locations", self.version_location)
        cfg.set_main_option("revision_environment", "true")
        cfg.set_section_option("post_write_hooks", "hooks", "dynamic_schema,import_postgresql,ruff")
        cfg.set_section_option("post_write_hooks", "dynamic_schema.type", "dynamic_schema")
        cfg.set_section_option("post_write_hooks", "import_postgresql.type", "import_postgresql")
        cfg.set_section_option("post_write_hooks", "ruff.type", "ruff")
        cfg.attributes["base"] = self.get_base()
        cfg.attributes["env_prefix"] = self.env_prefix
        self.import_models()
        return cfg


DATABASES: dict[str, DatabaseConfig] = {
    "richie": DatabaseConfig(
        env_prefix="RICHIE",
        version_location="python/alembic/richie/versions",
        base_module="python.orm.richie.base",
        base_class_name="RichieBase",
        models_module="python.orm.richie",
    ),
    "van_inventory": DatabaseConfig(
        env_prefix="VAN_INVENTORY",
        version_location="python/alembic/van_inventory/versions",
        base_module="python.orm.van_inventory.base",
        base_class_name="VanInventoryBase",
        models_module="python.orm.van_inventory.models",
    ),
}


app = typer.Typer(help="Multi-database alembic wrapper.")


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def main(
    ctx: typer.Context,
    db_name: Annotated[str, typer.Argument(help=f"Database name. Options: {', '.join(DATABASES)}")],
    command: Annotated[str, typer.Argument(help="Alembic command (upgrade, downgrade, revision, check, etc.)")],
) -> None:
    """Run an alembic command against the specified database."""
    db_config = DATABASES.get(db_name)
    if not db_config:
        typer.echo(f"Unknown database: {db_name!r}. Available: {', '.join(DATABASES)}", err=True)
        raise typer.Exit(code=1)

    alembic_cfg = db_config.alembic_config()

    cmd_line = CommandLine()
    options = cmd_line.parser.parse_args([command, *ctx.args])
    cmd_line.run_cmd(alembic_cfg, options)


if __name__ == "__main__":
    app()

