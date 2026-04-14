from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def check_gpu_free() -> None:
    """Warn if GPU-heavy processes (e.g. Ollama) are running."""
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.warning("Could not query GPU processes: %s", result.stderr.strip())
        return
    processes = result.stdout.strip()
    if processes:
        logger.warning("GPU processes detected:\n%s", processes)
        logger.warning("Consider stopping Ollama (sudo systemctl stop ollama) before benchmarking")
