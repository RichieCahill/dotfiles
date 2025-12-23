#!/usr/bin/env python3
"""fix_eval_warnings."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import requests
import typer

from python.common import configure_logger

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration for the script.

    Attributes:
        github_token (str): GitHub token for API authentication.
        model_name (str): The name of the LLM model to use. Defaults to "gpt-4o".
        api_base (str): The base URL for the GitHub Models API.
            Defaults to "https://models.inference.ai.azure.com".
    """

    github_token: str
    model_name: str = "gpt-4o"
    api_base: str = "https://models.inference.ai.azure.com"


def get_log_content(run_id: str) -> None:
    """Fetch the logs for a specific workflow run.

    Args:
        run_id (str): The run ID.
    """
    logger.info(f"Fetching logs for run ID: {run_id}")
    # List artifacts to find logs (or use jobs API)
    # For simplicity, we might need to use 'gh' cli in the workflow to download logs
    # But let's try to read from a file if passed as argument, which is easier for the workflow


def parse_warnings(log_file_path: Path) -> list[str]:
    """Parse the log file for evaluation warnings.

    Args:
        log_file_path (Path): The path to the log file.

    Returns:
        list[str]: A list of warning messages.
    """
    warnings = []
    with log_file_path.open(encoding="utf-8", errors="ignore") as f:
        warnings.extend(line.strip() for line in f if "evaluation warning:" in line)
    return warnings


def generate_fix(warning_msg: str, config: Config) -> str | None:
    """Call GitHub Models to generate a fix for the warning.

    Args:
        warning_msg (str): The warning message.
        config (Config): The configuration object.

    Returns:
        Optional[str]: The suggested fix or None.
    """
    logger.info(f"Generating fix for: {warning_msg}")

    prompt = f"""
    I encountered the following Nix evaluation warning:

    `{warning_msg}`

    Please explain what this warning means and suggest how to fix it in the Nix code.
    If possible, provide the exact code change in a diff format or a clear description of what to change.
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config.github_token}"}

    payload = {
        "messages": [
            {"role": "system", "content": "You are an expert NixOS and Nix language developer."},
            {"role": "user", "content": prompt},
        ],
        "model": config.model_name,
        "temperature": 0.1,
    }

    try:
        response = requests.post(f"{config.api_base}/chat/completions", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]  # type: ignore[no-any-return]
    except Exception:
        logger.exception("Error calling LLM")
        return None


def main(
    log_file: Path = typer.Argument(..., help="Path to the build log file"),  # noqa: B008
    model_name: str = typer.Option("gpt-4o", envvar="MODEL_NAME", help="LLM Model Name"),
) -> None:
    """Detect evaluation warnings in logs and suggest fixes using GitHub Models.

    Args:
        log_file (Path): Path to the build log file containing evaluation warnings.
        model_name (str): The name of the LLM model to use for generating fixes.
            Defaults to "gpt-4o", can be overridden by MODEL_NAME environment variable.
    """
    configure_logger()

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.warning("GITHUB_TOKEN not set. LLM calls will fail.")

    config = Config(github_token=github_token or "", model_name=model_name)

    if not log_file.exists():
        logger.error(f"Log file not found: {log_file}")
        raise typer.Exit(code=1)

    warnings = parse_warnings(log_file)
    if not warnings:
        logger.info("No evaluation warnings found.")
        raise typer.Exit(code=0)

    logger.info(f"Found {len(warnings)} warnings.")

    # Process unique warnings to save tokens
    unique_warnings = list(set(warnings))

    fixes = []
    for warning in unique_warnings:
        if not config.github_token:
            logger.warning("Skipping LLM call due to missing GITHUB_TOKEN")
            continue

        fix = generate_fix(warning, config)
        if fix:
            fixes.append(f"## Warning\n`{warning}`\n\n## Suggested Fix\n{fix}\n")

    # Output fixes to a markdown file for the PR body
    if fixes:
        with Path("fix_suggestions.md").open("w") as f:
            f.write("# Automated Fix Suggestions\n\n")
            f.write("\n---\n".join(fixes))
        logger.info("Fix suggestions written to fix_suggestions.md")
    else:
        logger.info("No fixes generated.")


app = typer.Typer()
app.command()(main)

if __name__ == "__main__":
    app()
