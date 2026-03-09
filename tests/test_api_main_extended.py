"""Extended tests for python/api/main.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from python.api.main import build_frontend, create_app


def test_build_frontend_runs_npm(tmp_path: Path) -> None:
    """Test build_frontend runs npm commands."""
    source_dir = tmp_path / "frontend"
    source_dir.mkdir()
    (source_dir / "package.json").write_text('{"name": "test"}')

    dist_dir = tmp_path / "build" / "dist"
    dist_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html></html>")

    def mock_copytree(src: Path, dst: Path, dirs_exist_ok: bool = False) -> None:
        if "dist" in str(src):
            Path(dst).mkdir(parents=True, exist_ok=True)
            (Path(dst) / "index.html").write_text("<html></html>")

    with (
        patch("python.api.main.subprocess.run") as mock_run,
        patch("python.api.main.shutil.copytree") as mock_copy,
        patch("python.api.main.shutil.rmtree"),
        patch("python.api.main.tempfile.mkdtemp") as mock_mkdtemp,
    ):
        # First mkdtemp for build dir, second for output dir
        build_dir = str(tmp_path / "build")
        output_dir = str(tmp_path / "output")
        mock_mkdtemp.side_effect = [build_dir, output_dir]

        # dist_dir exists check
        with patch("pathlib.Path.exists", return_value=True):
            result = build_frontend(source_dir, cache_dir=tmp_path / ".npm")

    assert mock_run.call_count == 2  # npm install + npm run build


def test_build_frontend_no_dist(tmp_path: Path) -> None:
    """Test build_frontend raises when dist directory not found."""
    source_dir = tmp_path / "frontend"
    source_dir.mkdir()
    (source_dir / "package.json").write_text('{"name": "test"}')

    with (
        patch("python.api.main.subprocess.run"),
        patch("python.api.main.shutil.copytree"),
        patch("python.api.main.tempfile.mkdtemp", return_value=str(tmp_path / "build")),
        pytest.raises(FileNotFoundError, match="Build output not found"),
    ):
        build_frontend(source_dir)


def test_create_app_includes_contact_router() -> None:
    """Test create_app includes contact router."""
    app = create_app()
    routes = [r.path for r in app.routes]
    # Should have API routes
    assert any("/api" in r for r in routes)
