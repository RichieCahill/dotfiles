"""Detect Nix evaluation warnings and create PRs with LLM-suggested fixes."""

from __future__ import annotations

import hashlib
import io
import logging
import re
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import httpx
import typer

from python.common import configure_logger

logger = logging.getLogger(__name__)


@dataclass
class EvalWarning:
    """A single Nix evaluation warning."""

    system: str
    message: str


@dataclass
class FileChange:
    """A file change suggested by the LLM."""

    file_path: str
    original: str
    fixed: str


WARNING_PATTERN = re.compile(r"(?:^[\d\-T:.Z]+ )?(warning:|trace: warning:)")
TIMESTAMP_PREFIX = re.compile(r"^[\d\-T:.Z]+ ")
NIX_STORE_PATH = re.compile(r"/nix/store/[^/]+-source/([^:]+\.nix)")
REPO_RELATIVE_PATH = re.compile(r"(?<![/\w])(systems|common|users|overlays)/[^:\s]+\.nix")
CHANGE_FILE_PATTERN = re.compile(r"^FILE:\s*(.+)$")


def run_cmd(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command and return the result.

    Args:
        cmd: Command and arguments.
        check: Whether to raise on non-zero exit.

    Returns:
        CompletedProcess with captured stdout/stderr.
    """
    logger.debug("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def download_logs(run_id: str, repo: str) -> dict[str, str]:
    """Download build logs for a GitHub Actions run.

    Args:
        run_id: The workflow run ID.
        repo: The GitHub repository (owner/repo).

    Returns:
        Dict mapping zip entry names to their text content, filtered to build log files.

    Raises:
        RuntimeError: If log download fails.
    """
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/actions/runs/{run_id}/logs"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        msg = f"Failed to download logs: {result.stderr.decode(errors='replace')}"
        raise RuntimeError(msg)

    logs: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(result.stdout)) as zf:
        for name in zf.namelist():
            if name.startswith("build-") and name.endswith(".txt"):
                logs[name] = zf.read(name).decode(errors="replace")

    return logs


def parse_warnings(logs: dict[str, str]) -> list[EvalWarning]:
    """Parse Nix evaluation warnings from build log contents.

    Args:
        logs: Dict mapping zip entry names (e.g. "build-bob/2_Build.txt") to their text.

    Returns:
        Deduplicated list of warnings.
    """
    warnings: list[EvalWarning] = []
    seen: set[str] = set()

    for name, content in sorted(logs.items()):
        system = name.split("/")[0].removeprefix("build-")
        for line in content.splitlines():
            if WARNING_PATTERN.search(line):
                message = TIMESTAMP_PREFIX.sub("", line).strip()
                key = f"{system}:{message}"
                if key not in seen:
                    seen.add(key)
                    warnings.append(EvalWarning(system=system, message=message))

    logger.info("Found %d unique warnings", len(warnings))
    return warnings


def extract_referenced_files(warnings: list[EvalWarning]) -> dict[str, str]:
    """Extract file paths referenced in warnings and read their contents.

    Args:
        warnings: List of parsed warnings.

    Returns:
        Dict mapping repo-relative file paths to their contents.
    """
    paths: set[str] = set()
    warning_text = "\n".join(w.message for w in warnings)

    for match in NIX_STORE_PATH.finditer(warning_text):
        paths.add(match.group(1))
    for match in REPO_RELATIVE_PATH.finditer(warning_text):
        paths.add(match.group(0))

    files: dict[str, str] = {}
    for path_str in sorted(paths):
        path = Path(path_str)
        if path.is_file():
            files[path_str] = path.read_text()

    if not files and Path("flake.nix").is_file():
        files["flake.nix"] = Path("flake.nix").read_text()

    logger.info("Extracted %d referenced files", len(files))
    return files


def compute_warning_hash(warnings: list[EvalWarning]) -> str:
    """Compute a short hash of the warning set for deduplication.

    Args:
        warnings: List of warnings.

    Returns:
        8-character hex hash.
    """
    text = "\n".join(sorted(f"[{w.system}] {w.message}" for w in warnings))
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def check_duplicate_pr(warning_hash: str) -> bool:
    """Check if an open PR already exists for this warning hash.

    Args:
        warning_hash: The hash to check.

    Returns:
        True if a duplicate PR exists.

    Raises:
        RuntimeError: If the gh CLI call fails.
    """
    result = run_cmd(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--label",
            "eval-warning-fix",
            "--json",
            "title",
            "--jq",
            ".[].title",
        ],
        check=False,
    )
    if result.returncode != 0:
        msg = f"Failed to check for duplicate PRs: {result.stderr}"
        raise RuntimeError(msg)

    for title in result.stdout.splitlines():
        if warning_hash in title:
            logger.info("Duplicate PR found for hash %s", warning_hash)
            return True
    return False


def query_ollama(
    warnings: list[EvalWarning],
    files: dict[str, str],
    ollama_url: str,
) -> str | None:
    """Query Ollama for a fix suggestion.

    Args:
        warnings: List of warnings.
        files: Referenced file contents.
        ollama_url: Ollama API base URL.

    Returns:
        LLM response text, or None on failure.
    """
    warning_text = "\n".join(f"[{w.system}] {w.message}" for w in warnings)
    file_context = "\n".join(f"--- FILE: {path} ---\n{content}\n--- END FILE ---" for path, content in files.items())

    prompt = f"""You are a NixOS configuration expert. \
Analyze the following Nix evaluation warnings and suggest fixes.

## Warnings
{warning_text}

## Referenced Files
{file_context}

## Instructions
- Identify the root cause of each warning
- Provide the exact file changes needed to fix the warnings
- Output your response in two clearly separated sections:
  1. **REASONING**: Brief explanation of what causes each warning and how to fix it
  2. **CHANGES**: For each file that needs changes, output a block like:
     FILE: path/to/file.nix
     <<<<<<< ORIGINAL
     the original lines to replace
     =======
     the replacement lines
     >>>>>>> FIXED
- Only suggest changes for files that exist in the repository
- Do not add unnecessary complexity
- Preserve the existing code style
- If a warning comes from upstream nixpkgs and cannot be fixed in this repo, \
say so in REASONING and do not suggest changes"""

    try:
        response = httpx.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "qwen3-coder:30b",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 4096},
            },
            timeout=300,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Ollama request failed")
        return None

    return response.json().get("response")


def parse_changes(response: str) -> list[FileChange]:
    """Parse file changes from the LLM response.

    Expects blocks in the format:
        FILE: path/to/file.nix
        <<<<<<< ORIGINAL
        ...
        =======
        ...
        >>>>>>> FIXED

    Args:
        response: Raw LLM response text.

    Returns:
        List of parsed file changes.
    """
    changes: list[FileChange] = []
    current_file = ""
    in_original = False
    in_fixed = False
    original_lines: list[str] = []
    fixed_lines: list[str] = []

    for line in response.splitlines():
        file_match = CHANGE_FILE_PATTERN.match(line)
        if file_match:
            current_file = file_match.group(1).strip()
        elif line.strip() == "<<<<<<< ORIGINAL":
            in_original = True
            in_fixed = False
            original_lines = []
        elif line.strip() == "=======" and in_original:
            in_original = False
            in_fixed = True
            fixed_lines = []
        elif line.strip() == ">>>>>>> FIXED" and in_fixed:
            in_fixed = False
            if current_file:
                changes.append(
                    FileChange(
                        file_path=current_file,
                        original="\n".join(original_lines),
                        fixed="\n".join(fixed_lines),
                    )
                )
        elif in_original:
            original_lines.append(line)
        elif in_fixed:
            fixed_lines.append(line)

    logger.info("Parsed %d file changes", len(changes))
    return changes


def apply_changes(changes: list[FileChange]) -> int:
    """Apply file changes to the working directory.

    Args:
        changes: List of changes to apply.

    Returns:
        Number of changes successfully applied.
    """
    applied = 0
    for change in changes:
        path = Path(change.file_path)
        if not path.is_file():
            logger.warning("File not found: %s", change.file_path)
            continue

        content = path.read_text()
        if change.original not in content:
            logger.warning("Original text not found in %s", change.file_path)
            continue

        path.write_text(content.replace(change.original, change.fixed, 1))
        logger.info("Applied fix to %s", change.file_path)
        applied += 1

    return applied


def create_pr(
    warning_hash: str,
    warnings: list[EvalWarning],
    llm_response: str,
    run_url: str,
) -> None:
    """Create a git branch and PR with the applied fixes.

    Args:
        warning_hash: Short hash for branch naming and deduplication.
        warnings: Original warnings for the PR body.
        llm_response: Full LLM response for extracting reasoning.
        run_url: URL to the triggering build run.
    """
    branch = f"fix/eval-warning-{warning_hash}"
    warning_text = "\n".join(f"[{w.system}] {w.message}" for w in warnings)

    reasoning_lines: list[str] = []
    capturing = False
    for line in llm_response.splitlines():
        if "**REASONING**" in line:
            capturing = True
        elif "**CHANGES**" in line:
            break
        elif capturing:
            reasoning_lines.append(line)
    reasoning = "\n".join(reasoning_lines[:50])

    run_cmd(["git", "config", "user.name", "github-actions[bot]"])
    run_cmd(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])
    run_cmd(["git", "checkout", "-b", branch])
    run_cmd(["git", "add", "-A"])

    diff_result = run_cmd(["git", "diff", "--cached", "--quiet"], check=False)
    if diff_result.returncode == 0:
        logger.info("No file changes to commit")
        return

    run_cmd(["git", "commit", "-m", f"fix: resolve nix evaluation warnings ({warning_hash})"])
    run_cmd(["git", "push", "origin", branch, "--force"])

    body = f"""## Nix Evaluation Warnings

Detected in [build_systems run]({run_url}):

```
{warning_text}
```

## LLM Analysis (qwen3-coder:30b)

{reasoning}

---
*Auto-generated by fix_eval_warnings. Review carefully before merging.*"""

    run_cmd(
        [
            "gh",
            "pr",
            "create",
            "--title",
            f"fix: resolve nix eval warnings ({warning_hash})",
            "--label",
            "automated",
            "--label",
            "eval-warning-fix",
            "--body",
            body,
        ]
    )
    logger.info("PR created on branch %s", branch)


def main(
    run_id: Annotated[str, typer.Option("--run-id", help="GitHub Actions run ID")],
    repo: Annotated[str, typer.Option("--repo", help="GitHub repository (owner/repo)")],
    ollama_url: Annotated[str, typer.Option("--ollama-url", help="Ollama API base URL")],
    run_url: Annotated[str, typer.Option("--run-url", help="URL to the triggering build run")],
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Log level")] = "INFO",
) -> None:
    """Detect Nix evaluation warnings and create PRs with LLM-suggested fixes."""
    configure_logger(log_level)

    logs = download_logs(run_id, repo)
    warnings = parse_warnings(logs)
    if not warnings:
        return

    warning_hash = compute_warning_hash(warnings)
    if check_duplicate_pr(warning_hash):
        return

    files = extract_referenced_files(warnings)
    llm_response = query_ollama(warnings, files, ollama_url)
    if not llm_response:
        return

    changes = parse_changes(llm_response)
    applied = apply_changes(changes)
    if applied == 0:
        logger.info("No changes could be applied")
        return

    create_pr(warning_hash, warnings, llm_response, run_url)


if __name__ == "__main__":
    typer.run(main)
