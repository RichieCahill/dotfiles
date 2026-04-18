"""Build and run the whisper transcription docker container on demand.

The container is started fresh for each invocation and removed on exit
(``docker run --rm``). The model is cached in a named docker volume so
only the first run pays the download cost.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from python.common import configure_logger

logger = logging.getLogger(__name__)


class Config:
    """Paths and names for the whisper-transcribe Docker workflow."""

    image_tag = "whisper-transcribe:latest"
    model_volume = "whisper-models"
    repo_root = Path(__file__).resolve().parents[3]
    dockerfile = Path(__file__).resolve().parent / "Dockerfile"
    huggingface_cache = "/root/.cache/huggingface"


def run_docker(arguments: list[str]) -> None:
    """Run a docker subcommand, streaming output and raising on failure.

    Args:
        arguments: Arguments to pass to the ``docker`` binary.

    Raises:
        subprocess.CalledProcessError: If docker exits non-zero.
    """
    logger.info("docker %s", " ".join(arguments))
    subprocess.run(["docker", *arguments], check=True)


def build_image() -> None:
    """Build the whisper-transcribe image using the repo root as build context."""
    logger.info("Building image %s", Config.image_tag)
    run_docker(
        [
            "build",
            "--tag",
            Config.image_tag,
            "--file",
            str(Config.dockerfile),
            str(Config.repo_root),
        ],
    )


def model_cache_present(model: str) -> bool:
    """Check whether the given model is already downloaded in the cache volume.

    Args:
        model: faster-whisper model name (e.g. ``large-v3``).

    Returns:
        True if the HuggingFace cache directory for the model exists in the volume.
    """
    cache_directory = f"hub/models--Systran--faster-whisper-{model}"
    completed = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{Config.model_volume}:/cache",
            "alpine",
            "test",
            "-d",
            f"/cache/{cache_directory}",
        ],
        check=False,
    )
    return completed.returncode == 0


def download_model(model: str) -> None:
    """Download the model into the cache volume and exit.

    Args:
        model: faster-whisper model name.
    """
    logger.info("Downloading model %s into volume %s", model, Config.model_volume)
    run_docker(
        [
            "run",
            "--rm",
            "--device=nvidia.com/gpu=all",
            "--ipc=host",
            "--volume",
            f"{Config.model_volume}:{Config.huggingface_cache}",
            Config.image_tag,
            "--model",
            model,
            "--download-only",
        ],
    )


def transcribe(input_directory: Path, output_directory: Path, model: str) -> None:
    """Run transcription on every audio file under ``input_directory``.

    Args:
        input_directory: Host path containing audio files (mounted read-only).
        output_directory: Host path for ``.txt`` transcripts.
        model: faster-whisper model name.
    """
    logger.info("Transcribing %s -> %s (model=%s)", input_directory, output_directory, model)
    run_docker(
        [
            "run",
            "--rm",
            "--device=nvidia.com/gpu=all",
            "--ipc=host",
            "--volume",
            f"{input_directory}:/audio:ro",
            "--volume",
            f"{output_directory}:/output",
            "--volume",
            f"{Config.model_volume}:{Config.huggingface_cache}",
            Config.image_tag,
            "--model",
            model,
        ],
    )


def main(
    input_directory: Annotated[Path, typer.Argument(help="Directory of audio files to transcribe.")],
    output_directory: Annotated[Path, typer.Argument(help="Directory to write .txt transcripts to.")],
    model: Annotated[str, typer.Option(help="faster-whisper model name.")] = "large-v3",
    *,
    force_download: Annotated[
        bool,
        typer.Option("--force-download", help="Re-download the model even if already cached."),
    ] = False,
) -> None:
    """Build the image, ensure the model is cached, then transcribe and stop."""
    configure_logger()

    resolved_input = input_directory.resolve(strict=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    resolved_output = output_directory.resolve()

    build_image()

    if force_download or not model_cache_present(model):
        download_model(model)
    else:
        logger.info("Model %s already cached in volume %s", model, Config.model_volume)

    transcribe(resolved_input, resolved_output, model)
    logger.info("Done. Container stopped.")


if __name__ == "__main__":
    typer.run(main)
