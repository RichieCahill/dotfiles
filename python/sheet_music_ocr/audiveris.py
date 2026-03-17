"""Audiveris subprocess wrapper for optical music recognition."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class AudiverisError(Exception):
    """Raised when Audiveris processing fails."""


def find_audiveris() -> str:
    """Find the Audiveris executable on PATH.

    Returns:
        Path to the audiveris executable.

    Raises:
        AudiverisError: If Audiveris is not found.
    """
    path = shutil.which("audiveris")
    if not path:
        msg = "Audiveris not found on PATH. Install it via 'nix develop' or add it to your environment."
        raise AudiverisError(msg)
    return path


def run_audiveris(input_path: Path, output_dir: Path) -> Path:
    """Run Audiveris on an input file and return the path to the generated .mxl.

    Args:
        input_path: Path to the input sheet music file (PDF, PNG, JPG, TIFF).
        output_dir: Directory where Audiveris will write its output.

    Returns:
        Path to the generated .mxl file.

    Raises:
        AudiverisError: If Audiveris fails or produces no output.
    """
    audiveris = find_audiveris()
    result = subprocess.run(
        [audiveris, "-batch", "-export", "-output", str(output_dir), str(input_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = f"Audiveris failed (exit {result.returncode}):\n{result.stderr}"
        raise AudiverisError(msg)

    mxl_files = list(output_dir.rglob("*.mxl"))
    if not mxl_files:
        msg = f"Audiveris produced no .mxl output in {output_dir}"
        raise AudiverisError(msg)

    return mxl_files[0]
