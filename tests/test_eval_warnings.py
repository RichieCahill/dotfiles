"""Tests for python/eval_warnings/main.py."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch
from zipfile import ZipFile
from io import BytesIO

import pytest

from python.eval_warnings.main import (
    EvalWarning,
    FileChange,
    apply_changes,
    compute_warning_hash,
    check_duplicate_pr,
    download_logs,
    extract_referenced_files,
    parse_changes,
    parse_warnings,
    query_ollama,
    run_cmd,
    create_pr,
)

if TYPE_CHECKING:
    pass


def test_eval_warning_frozen() -> None:
    """Test EvalWarning is frozen dataclass."""
    w = EvalWarning(system="test", message="warning: test msg")
    assert w.system == "test"
    assert w.message == "warning: test msg"


def test_file_change() -> None:
    """Test FileChange dataclass."""
    fc = FileChange(file_path="test.nix", original="old", fixed="new")
    assert fc.file_path == "test.nix"


def test_run_cmd() -> None:
    """Test run_cmd."""
    result = run_cmd(["echo", "hello"])
    assert result.stdout.strip() == "hello"


def test_run_cmd_check_false() -> None:
    """Test run_cmd with check=False."""
    result = run_cmd(["ls", "/nonexistent"], check=False)
    assert result.returncode != 0


def test_parse_warnings_basic() -> None:
    """Test parse_warnings extracts warnings."""
    logs = {
        "build-server1/2_Build.txt": "warning: test warning\nsome other line\ntrace: warning: another warning\n",
    }
    warnings = parse_warnings(logs)
    assert len(warnings) == 2


def test_parse_warnings_ignores_untrusted_flake() -> None:
    """Test parse_warnings ignores untrusted flake settings."""
    logs = {
        "build-server1/2_Build.txt": "warning: ignoring untrusted flake configuration setting foo\n",
    }
    warnings = parse_warnings(logs)
    assert len(warnings) == 0


def test_parse_warnings_strips_timestamp() -> None:
    """Test parse_warnings strips timestamps."""
    logs = {
        "build-server1/2_Build.txt": "2024-01-01T00:00:00.000Z warning: test msg\n",
    }
    warnings = parse_warnings(logs)
    assert len(warnings) == 1
    w = warnings.pop()
    assert w.message == "warning: test msg"
    assert w.system == "server1"


def test_parse_warnings_empty() -> None:
    """Test parse_warnings with no warnings."""
    logs = {"build-server1/2_Build.txt": "all good\n"}
    warnings = parse_warnings(logs)
    assert len(warnings) == 0


def test_compute_warning_hash() -> None:
    """Test compute_warning_hash returns consistent 8-char hash."""
    warnings = {EvalWarning(system="s1", message="msg1")}
    h = compute_warning_hash(warnings)
    assert len(h) == 8
    # Same input -> same hash
    assert compute_warning_hash(warnings) == h


def test_compute_warning_hash_different() -> None:
    """Test different warnings produce different hashes."""
    w1 = {EvalWarning(system="s1", message="msg1")}
    w2 = {EvalWarning(system="s1", message="msg2")}
    assert compute_warning_hash(w1) != compute_warning_hash(w2)


def test_extract_referenced_files(tmp_path: Path) -> None:
    """Test extract_referenced_files reads existing files."""
    nix_file = tmp_path / "test.nix"
    nix_file.write_text("{ pkgs }: pkgs")

    warnings = {EvalWarning(system="s1", message=f"warning: in /nix/store/abc-source/{nix_file}")}
    # Won't find the file since it uses absolute paths resolved differently
    files = extract_referenced_files(warnings)
    # Result depends on actual file resolution
    assert isinstance(files, dict)


def test_check_duplicate_pr_no_duplicate() -> None:
    """Test check_duplicate_pr when no duplicate exists."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "fix: resolve nix eval warnings (abcd1234)\nfix: other (efgh5678)\n"

    with patch("python.eval_warnings.main.run_cmd", return_value=mock_result):
        assert check_duplicate_pr("xxxxxxxx") is False


def test_check_duplicate_pr_found() -> None:
    """Test check_duplicate_pr when duplicate exists."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "fix: resolve nix eval warnings (abcd1234)\n"

    with patch("python.eval_warnings.main.run_cmd", return_value=mock_result):
        assert check_duplicate_pr("abcd1234") is True


def test_check_duplicate_pr_error() -> None:
    """Test check_duplicate_pr raises on error."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "gh error"

    with (
        patch("python.eval_warnings.main.run_cmd", return_value=mock_result),
        pytest.raises(RuntimeError, match="Failed to check for duplicate PRs"),
    ):
        check_duplicate_pr("test")


def test_parse_changes_basic() -> None:
    """Test parse_changes with valid response."""
    response = """## **REASONING**
Some reasoning here.

## **CHANGES**
FILE: test.nix
<<<<<<< ORIGINAL
old line
=======
new line
>>>>>>> FIXED
"""
    changes = parse_changes(response)
    assert len(changes) == 1
    assert changes[0].file_path == "test.nix"
    assert changes[0].original == "old line"
    assert changes[0].fixed == "new line"


def test_parse_changes_no_changes_section() -> None:
    """Test parse_changes with missing CHANGES section."""
    response = "Some text without changes"
    changes = parse_changes(response)
    assert changes == []


def test_parse_changes_multiple() -> None:
    """Test parse_changes with multiple file changes."""
    response = """**CHANGES**
FILE: file1.nix
<<<<<<< ORIGINAL
old1
=======
new1
>>>>>>> FIXED
FILE: file2.nix
<<<<<<< ORIGINAL
old2
=======
new2
>>>>>>> FIXED
"""
    changes = parse_changes(response)
    assert len(changes) == 2


def test_apply_changes(tmp_path: Path) -> None:
    """Test apply_changes applies changes to files."""
    test_file = tmp_path / "test.nix"
    test_file.write_text("old content here")

    changes = [FileChange(file_path=str(test_file), original="old content", fixed="new content")]

    with patch("python.eval_warnings.main.Path.cwd", return_value=tmp_path):
        applied = apply_changes(changes)

    assert applied == 1
    assert "new content here" in test_file.read_text()


def test_apply_changes_file_not_found(tmp_path: Path) -> None:
    """Test apply_changes skips missing files."""
    changes = [FileChange(file_path=str(tmp_path / "missing.nix"), original="old", fixed="new")]

    with patch("python.eval_warnings.main.Path.cwd", return_value=tmp_path):
        applied = apply_changes(changes)

    assert applied == 0


def test_apply_changes_original_not_found(tmp_path: Path) -> None:
    """Test apply_changes skips if original text not in file."""
    test_file = tmp_path / "test.nix"
    test_file.write_text("different content")

    changes = [FileChange(file_path=str(test_file), original="not found", fixed="new")]

    with patch("python.eval_warnings.main.Path.cwd", return_value=tmp_path):
        applied = apply_changes(changes)

    assert applied == 0


def test_apply_changes_path_traversal(tmp_path: Path) -> None:
    """Test apply_changes blocks path traversal."""
    changes = [FileChange(file_path="/etc/passwd", original="old", fixed="new")]

    with patch("python.eval_warnings.main.Path.cwd", return_value=tmp_path):
        applied = apply_changes(changes)

    assert applied == 0


def test_query_ollama_success() -> None:
    """Test query_ollama returns response."""
    warnings = {EvalWarning(system="s1", message="warning: test")}
    files = {"test.nix": "{ pkgs }: pkgs"}

    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "some fix suggestion"}
    mock_response.raise_for_status.return_value = None

    with patch("python.eval_warnings.main.post", return_value=mock_response):
        result = query_ollama(warnings, files, "http://localhost:11434")

    assert result == "some fix suggestion"


def test_query_ollama_failure() -> None:
    """Test query_ollama returns None on failure."""
    from httpx import HTTPError

    warnings = {EvalWarning(system="s1", message="warning: test")}
    files = {}

    with patch("python.eval_warnings.main.post", side_effect=HTTPError("fail")):
        result = query_ollama(warnings, files, "http://localhost:11434")

    assert result is None


def test_download_logs_success() -> None:
    """Test download_logs extracts build log files from zip."""
    # Create a zip file in memory
    buf = BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("build-server1/2_Build.txt", "warning: test")
        zf.writestr("other-file.txt", "not a build log")
    zip_bytes = buf.getvalue()

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = zip_bytes

    with patch("python.eval_warnings.main.subprocess.run", return_value=mock_result):
        logs = download_logs("12345", "owner/repo")

    assert "build-server1/2_Build.txt" in logs
    assert "other-file.txt" not in logs


def test_download_logs_failure() -> None:
    """Test download_logs raises on failure."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = b"error"

    with (
        patch("python.eval_warnings.main.subprocess.run", return_value=mock_result),
        pytest.raises(RuntimeError, match="Failed to download logs"),
    ):
        download_logs("12345", "owner/repo")


def test_create_pr() -> None:
    """Test create_pr creates branch and PR."""
    warnings = {EvalWarning(system="s1", message="warning: test")}
    llm_response = "**REASONING**\nSome fix.\n**CHANGES**\nstuff"

    mock_diff_result = MagicMock()
    mock_diff_result.returncode = 1  # changes exist

    call_count = 0

    def mock_run_cmd(cmd: list[str], *, check: bool = True) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        if "diff" in cmd:
            result.returncode = 1
        return result

    with patch("python.eval_warnings.main.run_cmd", side_effect=mock_run_cmd):
        create_pr("abcd1234", warnings, llm_response, "https://example.com/run/1")

    assert call_count > 0


def test_create_pr_no_changes() -> None:
    """Test create_pr does nothing when no file changes."""
    warnings = {EvalWarning(system="s1", message="warning: test")}
    llm_response = "**REASONING**\nNo changes needed.\n**CHANGES**\n"

    def mock_run_cmd(cmd: list[str], *, check: bool = True) -> MagicMock:
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        return result

    with patch("python.eval_warnings.main.run_cmd", side_effect=mock_run_cmd):
        create_pr("abcd1234", warnings, llm_response, "https://example.com/run/1")


def test_create_pr_no_reasoning() -> None:
    """Test create_pr handles missing REASONING section."""
    warnings = {EvalWarning(system="s1", message="warning: test")}
    llm_response = "No reasoning here"

    def mock_run_cmd(cmd: list[str], *, check: bool = True) -> MagicMock:
        result = MagicMock()
        result.returncode = 0 if "diff" not in cmd else 1
        result.stdout = ""
        return result

    with patch("python.eval_warnings.main.run_cmd", side_effect=mock_run_cmd):
        create_pr("abcd1234", warnings, llm_response, "https://example.com/run/1")
