"""Docker container lifecycle management for vLLM."""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)

CONTAINER_NAME = "vllm-bench"
VLLM_IMAGE = "vllm/vllm-openai:v0.19.0"


def start_vllm(
    *,
    model: str,
    port: int,
    model_dir: str,
    gpu_memory_utilization: float,
) -> None:
    """Start a vLLM container serving the given model.

    Args:
        model: HuggingFace model directory name (relative to model_dir).
        port: Host port to bind.
        model_dir: Host path containing HuggingFace model directories.
        gpu_memory_utilization: Fraction of GPU memory to use (0-1).
    """
    command = [
        "docker",
        "run",
        "-d",
        "--name",
        CONTAINER_NAME,
        "--device=nvidia.com/gpu=all",
        "--ipc=host",
        "-v",
        f"{model_dir}:/models",
        "-p",
        f"{port}:8000",
        VLLM_IMAGE,
        "--model",
        f"/models/{model}",
        "--served-model-name",
        model,
        "--gpu-memory-utilization",
        str(gpu_memory_utilization),
        "--max-model-len",
        "4096",
    ]
    logger.info("Starting vLLM container with model: %s", model)
    stop_vllm()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        msg = f"Failed to start vLLM container: {result.stderr.strip()}"
        raise RuntimeError(msg)
    logger.info("vLLM container started: %s", result.stdout.strip()[:12])


def stop_vllm() -> None:
    """Stop and remove the vLLM benchmark container."""
    logger.info("Stopping vLLM container")
    subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True, check=False)
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True, check=False)
    subprocess.run(
        ["docker", "network", "disconnect", "-f", "bridge", CONTAINER_NAME],
        capture_output=True,
        check=False,
    )
    logger.info("vLLM container stopped and removed")
