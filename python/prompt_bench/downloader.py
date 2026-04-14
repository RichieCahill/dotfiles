"""HuggingFace model downloader."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from huggingface_hub import snapshot_download

from python.prompt_bench.models import BenchmarkConfig

logger = logging.getLogger(__name__)


def local_model_path(repo: str, model_dir: str) -> Path:
    """Return the local directory path for a HuggingFace repo."""
    return Path(model_dir) / repo


def is_model_present(repo: str, model_dir: str) -> bool:
    """Check if a model has already been downloaded."""
    path = local_model_path(repo, model_dir)
    return path.exists() and any(path.iterdir())


def download_model(repo: str, model_dir: str) -> Path:
    """Download a HuggingFace model to the local model directory.

    Skips the download if the model directory already exists and contains files.
    """
    local_path = local_model_path(repo, model_dir)

    if is_model_present(repo, model_dir):
        logger.info("Model already exists: %s", local_path)
        return local_path

    logger.info("Downloading model: %s -> %s", repo, local_path)
    snapshot_download(
        repo_id=repo,
        local_dir=str(local_path),
    )
    logger.info("Download complete: %s", repo)
    return local_path


def download_all(config: BenchmarkConfig) -> None:
    """Download every model listed in the config, top to bottom."""
    for repo in config.models:
        download_model(repo, config.model_dir)


def main(
    config: Annotated[Path, typer.Option(help="Path to TOML config file")] = Path("bench.toml"),
    log_level: Annotated[str, typer.Option(help="Log level")] = "INFO",
) -> None:
    """Download all models listed in the benchmark config."""
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if not config.is_file():
        message = f"Config file does not exist: {config}"
        raise typer.BadParameter(message)

    benchmark_config = BenchmarkConfig.from_toml(config)
    download_all(benchmark_config)


def cli() -> None:
    """Typer entry point."""
    typer.run(main)


if __name__ == "__main__":
    cli()
