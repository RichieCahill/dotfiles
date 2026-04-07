"""Pydantic models for benchmark configuration."""

from __future__ import annotations

from pydantic import BaseModel


class BenchmarkConfig(BaseModel):
    """Top-level benchmark configuration loaded from TOML."""

    models: list[str]
    model_dir: str = "/zfs/models/hf"
    port: int = 8000
    gpu_memory_utilization: float = 0.90
    temperature: float = 0.0
    timeout: int = 300
    concurrency: int = 4
