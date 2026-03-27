"""Count lines of code in the repository, grouped by file type."""

from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path


def get_tracked_files() -> list[str]:
    """Get all git-tracked files."""
    result = subprocess.run(
        ["git", "ls-files"],  # noqa: S603, S607
        capture_output=True,
        text=True,
        check=True,
    )
    return [f for f in result.stdout.strip().splitlines() if f]


def count_lines(filepath: str) -> int:
    """Count lines in a file, returning 0 for binary files."""
    try:
        return len(Path(filepath).read_text(encoding="utf-8").splitlines())
    except (UnicodeDecodeError, OSError):
        return 0


def count_lines_by_type() -> dict[str, int]:
    """Count lines grouped by file extension."""
    lines_by_type: dict[str, int] = defaultdict(int)
    for filepath in get_tracked_files():
        ext = Path(filepath).suffix.lstrip(".")
        if not ext:
            ext = Path(filepath).name
        lines_by_type[ext] += count_lines(filepath)
    # Exclude binary/non-code files
    for key in ("png", "lock"):
        lines_by_type.pop(key, None)
    return dict(sorted(lines_by_type.items(), key=lambda x: x[1], reverse=True))


def format_report() -> str:
    """Generate a formatted line count report."""
    lines_by_type = count_lines_by_type()
    total = sum(lines_by_type.values())

    lines = [
        f"This repo has **{total:,}** lines of technical debt.",
        "",
        "| File Type | Lines | Percentage |",
        "|-----------|------:|-----------:|",
    ]
    for ext, count in lines_by_type.items():
        if count > 0:
            pct = count / total * 100
            prefix = "." if not ext.startswith(".") else ""
            lines.append(f"| {prefix}{ext} | {count:,} | {pct:.1f}% |")

    return "\n".join(lines)


def update_readme() -> None:
    """Update README.md with the line count report."""
    readme_path = Path("README.md")
    report = format_report()

    start_marker = "<!-- LINE-COUNT-START -->"
    end_marker = "<!-- LINE-COUNT-END -->"

    content = readme_path.read_text(encoding="utf-8")

    section = f"{start_marker}\n{report}\n{end_marker}"

    if start_marker in content:
        start = content.index(start_marker)
        end = content.index(end_marker) + len(end_marker)
        content = content[:start] + section + content[end:]
    else:
        content = content.rstrip() + "\n\n" + section + "\n"

    readme_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    update_readme()
