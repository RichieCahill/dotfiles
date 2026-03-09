"""Tests for api/main.py serve function and frontend router."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from python.api.main import build_frontend, create_app, serve


def test_build_frontend_none_source() -> None:
    """Test build_frontend returns None when no source dir."""
    result = build_frontend(None)
    assert result is None


def test_build_frontend_nonexistent_dir(tmp_path: Path) -> None:
    """Test build_frontend raises for nonexistent directory."""
    with pytest.raises(FileExistsError):
        build_frontend(tmp_path / "nonexistent")


def test_create_app_with_frontend(tmp_path: Path) -> None:
    """Test create_app with frontend directory."""
    # Create a minimal frontend dir with assets
    assets = tmp_path / "assets"
    assets.mkdir()
    (tmp_path / "index.html").write_text("<html></html>")

    app = create_app(frontend_dir=tmp_path)
    routes = [r.path for r in app.routes]
    assert any("/api" in r for r in routes)


def test_serve_calls_uvicorn() -> None:
    """Test serve function calls uvicorn.run."""
    with (
        patch("python.api.main.uvicorn.run") as mock_run,
        patch("python.api.main.build_frontend", return_value=None),
        patch("python.api.main.configure_logger"),
        patch.dict("os.environ", {"HOME": "/tmp"}),
    ):
        serve(host="localhost", port=8000, log_level="INFO")
        mock_run.assert_called_once()


def test_serve_with_frontend_dir(tmp_path: Path) -> None:
    """Test serve function with frontend dir."""
    assets = tmp_path / "assets"
    assets.mkdir()
    (tmp_path / "index.html").write_text("<html></html>")
    with (
        patch("python.api.main.uvicorn.run") as mock_run,
        patch("python.api.main.build_frontend", return_value=tmp_path),
        patch("python.api.main.configure_logger"),
        patch.dict("os.environ", {"HOME": "/tmp"}),
    ):
        serve(host="localhost", frontend_dir=tmp_path, port=8000, log_level="INFO")
        mock_run.assert_called_once()
