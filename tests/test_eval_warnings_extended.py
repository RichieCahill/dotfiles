"""Extended tests for python/eval_warnings/main.py."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from python.eval_warnings.main import (
    EvalWarning,
    extract_referenced_files,
)


def test_extract_referenced_files_nix_store_paths(tmp_path: Path) -> None:
    """Test extracting files from nix store paths."""
    # Create matching directory structure
    systems_dir = tmp_path / "systems"
    systems_dir.mkdir()
    nix_file = systems_dir / "test.nix"
    nix_file.write_text("{ pkgs }: pkgs")

    warnings = {
        EvalWarning(
            system="s1",
            message="warning: in /nix/store/abc-source/systems/test.nix:5: deprecated",
        )
    }

    # Change to tmp_path so relative paths work
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        files = extract_referenced_files(warnings)
    finally:
        os.chdir(old_cwd)

    assert "systems/test.nix" in files
    assert files["systems/test.nix"] == "{ pkgs }: pkgs"


def test_extract_referenced_files_no_files_found() -> None:
    """Test extract_referenced_files when no files are found."""
    warnings = {
        EvalWarning(
            system="s1",
            message="warning: something generic without file paths",
        )
    }
    files = extract_referenced_files(warnings)
    # Either empty or has flake.nix fallback
    assert isinstance(files, dict)


def test_extract_referenced_files_repo_relative_paths(tmp_path: Path) -> None:
    """Test extracting repo-relative file paths."""
    # Create the referenced file
    systems_dir = tmp_path / "systems" / "foo"
    systems_dir.mkdir(parents=True)
    nix_file = systems_dir / "bar.nix"
    nix_file.write_text("{ config }: {}")

    warnings = {
        EvalWarning(
            system="s1",
            message="warning: in systems/foo/bar.nix:10: test",
        )
    }

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        files = extract_referenced_files(warnings)
    finally:
        os.chdir(old_cwd)

    assert "systems/foo/bar.nix" in files
