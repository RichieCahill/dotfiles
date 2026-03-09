"""Tests for eval_warnings/main.py main() entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_eval_warnings_main_no_warnings() -> None:
    """Test main() when no warnings are found."""
    from python.eval_warnings.main import main

    with (
        patch("python.eval_warnings.main.configure_logger"),
        patch("python.eval_warnings.main.download_logs", return_value="clean log"),
        patch("python.eval_warnings.main.parse_warnings", return_value=set()),
    ):
        main(
            run_id="123",
            repo="owner/repo",
            ollama_url="http://localhost:11434",
            run_url="http://example.com/run",
            log_level="INFO",
        )


def test_eval_warnings_main_duplicate_pr() -> None:
    """Test main() when a duplicate PR exists."""
    from python.eval_warnings.main import main, EvalWarning

    warnings = {EvalWarning(system="s1", message="test")}
    with (
        patch("python.eval_warnings.main.configure_logger"),
        patch("python.eval_warnings.main.download_logs", return_value="log"),
        patch("python.eval_warnings.main.parse_warnings", return_value=warnings),
        patch("python.eval_warnings.main.compute_warning_hash", return_value="abc123"),
        patch("python.eval_warnings.main.check_duplicate_pr", return_value=True),
    ):
        main(
            run_id="123",
            repo="owner/repo",
            ollama_url="http://localhost:11434",
            run_url="http://example.com/run",
        )


def test_eval_warnings_main_no_llm_response() -> None:
    """Test main() when LLM returns no response."""
    from python.eval_warnings.main import main, EvalWarning

    warnings = {EvalWarning(system="s1", message="test")}
    with (
        patch("python.eval_warnings.main.configure_logger"),
        patch("python.eval_warnings.main.download_logs", return_value="log"),
        patch("python.eval_warnings.main.parse_warnings", return_value=warnings),
        patch("python.eval_warnings.main.compute_warning_hash", return_value="abc123"),
        patch("python.eval_warnings.main.check_duplicate_pr", return_value=False),
        patch("python.eval_warnings.main.extract_referenced_files", return_value={}),
        patch("python.eval_warnings.main.query_ollama", return_value=None),
    ):
        main(
            run_id="123",
            repo="owner/repo",
            ollama_url="http://localhost:11434",
            run_url="http://example.com/run",
        )


def test_eval_warnings_main_no_changes_applied() -> None:
    """Test main() when no changes are applied."""
    from python.eval_warnings.main import main, EvalWarning

    warnings = {EvalWarning(system="s1", message="test")}
    with (
        patch("python.eval_warnings.main.configure_logger"),
        patch("python.eval_warnings.main.download_logs", return_value="log"),
        patch("python.eval_warnings.main.parse_warnings", return_value=warnings),
        patch("python.eval_warnings.main.compute_warning_hash", return_value="abc123"),
        patch("python.eval_warnings.main.check_duplicate_pr", return_value=False),
        patch("python.eval_warnings.main.extract_referenced_files", return_value={}),
        patch("python.eval_warnings.main.query_ollama", return_value="some response"),
        patch("python.eval_warnings.main.parse_changes", return_value=[]),
        patch("python.eval_warnings.main.apply_changes", return_value=0),
    ):
        main(
            run_id="123",
            repo="owner/repo",
            ollama_url="http://localhost:11434",
            run_url="http://example.com/run",
        )


def test_eval_warnings_main_full_success() -> None:
    """Test main() full success path."""
    from python.eval_warnings.main import main, EvalWarning

    warnings = {EvalWarning(system="s1", message="test")}
    with (
        patch("python.eval_warnings.main.configure_logger"),
        patch("python.eval_warnings.main.download_logs", return_value="log"),
        patch("python.eval_warnings.main.parse_warnings", return_value=warnings),
        patch("python.eval_warnings.main.compute_warning_hash", return_value="abc123"),
        patch("python.eval_warnings.main.check_duplicate_pr", return_value=False),
        patch("python.eval_warnings.main.extract_referenced_files", return_value={}),
        patch("python.eval_warnings.main.query_ollama", return_value="response"),
        patch("python.eval_warnings.main.parse_changes", return_value=[{"file": "a.nix"}]),
        patch("python.eval_warnings.main.apply_changes", return_value=1),
        patch("python.eval_warnings.main.create_pr") as mock_pr,
    ):
        main(
            run_id="123",
            repo="owner/repo",
            ollama_url="http://localhost:11434",
            run_url="http://example.com/run",
        )
        mock_pr.assert_called_once()
