"""Pydantic models for benchmark configuration."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from pathlib import Path


class BenchmarkConfig(BaseModel):
    """Top-level benchmark configuration loaded from TOML."""

    models: list[str]
    model_dir: str = "/zfs/models/hf"
    port: int = 8000
    gpu_memory_utilization: float = 0.90
    temperature: float = 0.0
    timeout: int = 300
    concurrency: int = 4
    vllm_startup_timeout: int = 900

    @classmethod
    def from_toml(cls, config_path: Path) -> BenchmarkConfig:
        """Load benchmark config from a TOML file."""
        raw = tomllib.loads(config_path.read_text())["bench"]
        return cls(**raw)
