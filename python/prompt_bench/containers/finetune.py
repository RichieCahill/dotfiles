"""Docker container lifecycle management for Unsloth fine-tuning."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from python.prompt_bench.containers.lib import check_gpu_free

logger = logging.getLogger(__name__)

CONTAINER_NAME = "bill-finetune"
FINETUNE_IMAGE = "bill-finetune:latest"
DOCKERFILE_PATH = "/home/richie/dotfiles/python/prompt_bench/Dockerfile.finetune"
DEFAULT_HF_CACHE = Path("/zfs/models/hf")


def build_image() -> None:
    """Build the fine-tuning Docker image."""
    logger.info("Building fine-tuning image: %s", FINETUNE_IMAGE)
    result = subprocess.run(
        ["docker", "build", "-f", DOCKERFILE_PATH, "-t", FINETUNE_IMAGE, "."],
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = "Failed to build fine-tuning image"
        raise RuntimeError(message)
    logger.info("Image built: %s", FINETUNE_IMAGE)


def start_finetune(
    *,
    dataset_path: Path,
    output_dir: Path,
    hf_cache: Path = DEFAULT_HF_CACHE,
) -> None:
    """Run the fine-tuning container.

    Args:
        dataset_path: Host path to the fine-tuning JSONL dataset.
        output_dir: Host path where the trained model will be saved.
        hf_cache: Host path to HuggingFace model cache (bind-mounted to avoid re-downloading).
        validation_split: Fraction of data held out for validation.
    """
    dataset_path = dataset_path.resolve()
    output_dir = output_dir.resolve()

    if not dataset_path.is_file():
        message = f"Dataset not found: {dataset_path}"
        raise FileNotFoundError(message)

    output_dir.mkdir(parents=True, exist_ok=True)
    stop_finetune()

    hf_cache = hf_cache.resolve()
    hf_cache.mkdir(parents=True, exist_ok=True)

    command = [
        "docker",
        "run",
        "--name",
        CONTAINER_NAME,
        "--device=nvidia.com/gpu=all",
        "--ipc=host",
        "-v",
        f"{hf_cache}:/root/.cache/huggingface",
        "-v",
        f"{output_dir}:/workspace/output/qwen-bill-summarizer",
        "-v",
        f"{dataset_path}:/workspace/dataset.jsonl:ro",
        FINETUNE_IMAGE,
        "--dataset",
        "/workspace/dataset.jsonl",
        "--output-dir",
        "/workspace/output/qwen-bill-summarizer",
    ]

    logger.info("Starting fine-tuning container")
    logger.info("  Dataset:    %s", dataset_path)
    logger.info("  Output:     %s", output_dir)

    result = subprocess.run(command, text=True, check=False)
    if result.returncode != 0:
        message = f"Fine-tuning container exited with code {result.returncode}"
        raise RuntimeError(message)
    logger.info("Fine-tuning complete. Model saved to %s", output_dir)


def stop_finetune() -> None:
    """Stop and remove the fine-tuning container."""
    logger.info("Stopping fine-tuning container")
    subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True, check=False)
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True, check=False)


def logs_finetune() -> str | None:
    """Return recent logs from the fine-tuning container, or None if not running."""
    result = subprocess.run(
        ["docker", "logs", "--tail", "50", CONTAINER_NAME],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout + result.stderr


app = typer.Typer(help="Fine-tuning container management.")


@app.command()
def build() -> None:
    """Build the fine-tuning Docker image."""
    build_image()


@app.command()
def run(
    dataset: Annotated[Path, typer.Option(help="Fine-tuning JSONL")] = Path(
        "/home/richie/dotfiles/data/finetune_dataset.jsonl"
    ),
    output_dir: Annotated[Path, typer.Option(help="Where to save the trained model")] = Path(
        "/home/richie/dotfiles/data/output/qwen-bill-summarizer",
    ),
    hf_cache: Annotated[Path, typer.Option(help="Host path to HuggingFace model cache")] = DEFAULT_HF_CACHE,
    log_level: Annotated[str, typer.Option(help="Log level")] = "INFO",
) -> None:
    """Run fine-tuning inside a Docker container."""
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    check_gpu_free()
    start_finetune(
        dataset_path=dataset,
        output_dir=output_dir,
        hf_cache=hf_cache,
    )

@app.command()
def stop() -> None:
    """Stop and remove the fine-tuning container."""
    stop_finetune()


@app.command()
def logs() -> None:
    """Show recent logs from the fine-tuning container."""
    output = logs_finetune()
    if output is None:
        typer.echo("No running fine-tuning container found.")
        raise typer.Exit(code=1)
    typer.echo(output)


def cli() -> None:
    """Typer entry point."""
    app()


if __name__ == "__main__":
    cli()
