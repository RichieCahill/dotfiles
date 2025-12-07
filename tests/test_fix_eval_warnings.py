"""test_fix_eval_warnings."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from python.tools.fix_eval_warnings import Config, app, generate_fix, parse_warnings
from tests.conftest import TOKEN

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture

runner = CliRunner()


def test_parse_warnings(fs: FakeFilesystem) -> None:
    """test_parse_warnings."""
    log_file = Path("/build.log")
    fs.create_file(
        log_file,
        contents="Some output\nevaluation warning: 'system' is deprecated\nMore output",
        encoding="utf-8",
    )
    warnings = parse_warnings(log_file)
    assert len(warnings) == 1
    assert warnings[0] == "evaluation warning: 'system' is deprecated"


def test_generate_fix(mocker: MockerFixture) -> None:
    """test_generate_fix."""
    mock_post = mocker.patch("python.tools.fix_eval_warnings.requests.post")
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Use stdenv.hostPlatform.system"}}]
    }
    mock_post.return_value = mock_response

    config = Config(github_token=TOKEN)
    fix = generate_fix("evaluation warning: 'system' is deprecated", config)

    assert fix == "Use stdenv.hostPlatform.system"
    mock_post.assert_called_once()


def test_main(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """test_main."""
    log_file = Path("/build.log")
    fs.create_file(
        log_file,
        contents="Some output\nevaluation warning: 'system' is deprecated\nMore output",
        encoding="utf-8",
    )

    mock_generate_fix = mocker.patch("python.tools.fix_eval_warnings.generate_fix")
    mock_generate_fix.return_value = "Fixed it"
    mock_logger = mocker.patch("python.tools.fix_eval_warnings.logger")

    # We need to mock GITHUB_TOKEN env var or the script will warn/fail
    mocker.patch.dict("os.environ", {"GITHUB_TOKEN": TOKEN})

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
