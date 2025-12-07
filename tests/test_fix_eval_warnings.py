"""Tests for fix_eval_warnings."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from python.tools.fix_eval_warnings import Config, app, generate_fix, parse_warnings

runner = CliRunner()


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    """Create a dummy log file."""
    log_path = tmp_path / "build.log"
    log_path.write_text("Some output\nevaluation warning: 'system' is deprecated\nMore output", encoding="utf-8")
    return log_path


def test_parse_warnings(log_file: Path) -> None:
    """Test parsing warnings from a log file."""
    warnings = parse_warnings(log_file)
    assert len(warnings) == 1
    assert warnings[0] == "evaluation warning: 'system' is deprecated"


@patch("python.tools.fix_eval_warnings.requests.post")
def test_generate_fix(mock_post: MagicMock) -> None:
    """Test generating a fix."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Use stdenv.hostPlatform.system"}}]}
    mock_post.return_value = mock_response

    config = Config(github_token="dummy_token")
    fix = generate_fix("evaluation warning: 'system' is deprecated", config)

    assert fix == "Use stdenv.hostPlatform.system"
    mock_post.assert_called_once()


@patch("python.tools.fix_eval_warnings.logger")
@patch("python.tools.fix_eval_warnings.generate_fix")
def test_main(mock_generate_fix: MagicMock, mock_logger: MagicMock, log_file: Path) -> None:
    """Test the main CLI."""
    mock_generate_fix.return_value = "Fixed it"

    # We need to mock GITHUB_TOKEN env var or the script will warn/fail
    with patch.dict("os.environ", {"GITHUB_TOKEN": "dummy"}):
        result = runner.invoke(app, [str(log_file)])

    assert result.exit_code == 0
    # Verify logger calls instead of stdout, as CliRunner might not capture logging output correctly
    # when logging is configured to write to sys.stdout directly.
    assert any("Found 1 warnings" in str(call) for call in mock_logger.info.call_args_list)
    assert any(
        "Fix suggestions written to fix_suggestions.md" in str(call)
        for call in mock_logger.info.call_args_list
    )
    assert Path("fix_suggestions.md").exists()
    Path("fix_suggestions.md").unlink()
