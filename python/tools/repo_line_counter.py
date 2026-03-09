"""Count lines of code in a local directory, grouped by file extension."""

import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(help="Count lines of code by file extension.")

MAX_DISPLAY_EXTENSIONS = 10

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".exe",
    ".bin",
    ".so",
    ".dylib",
    ".dll",
    ".o",
    ".a",
    ".pyc",
    ".class",
    ".jar",
}


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git")
    if not git:
        msg = "git not found on PATH"
        raise typer.BadParameter(msg)
    return subprocess.run(
        [git, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )


def get_git_files(directory: Path) -> set[Path]:
    """Get the set of files tracked/not-ignored by git."""
    result = _git("ls-files", "--cached", "--others", "--exclude-standard", cwd=directory)
    if result.returncode != 0:
        msg = f"Not a git repository or git error: {directory}"
        raise typer.BadParameter(msg)
    return {directory / line for line in result.stdout.splitlines()}


def count_lines(target: Path, *, respect_gitignore: bool) -> dict[str, int]:
    """Walk a directory and count lines per file extension."""
    if respect_gitignore:
        allowed_files = get_git_files(target)

    counts: dict[str, int] = defaultdict(int)
    for filepath in target.rglob("*"):
        if not filepath.is_file():
            continue
        if respect_gitignore and filepath not in allowed_files:
            continue
        ext = filepath.suffix or "(no extension)"
        if ext in BINARY_EXTENSIONS:
            continue
        try:
            lines = filepath.read_text(encoding="utf-8", errors="ignore").count("\n")
            counts[ext] += lines
        except OSError:
            continue
    return dict(counts)


def get_first_commit_date(directory: Path) -> datetime:
    """Get the date of the first commit in the repo."""
    result = _git("log", "--reverse", "--format=%aI", cwd=directory)
    if result.returncode != 0 or not result.stdout.strip():
        msg = f"Could not read git history: {directory}"
        raise typer.BadParameter(msg)
    first_line = result.stdout.splitlines()[0]
    return datetime.fromisoformat(first_line)


def get_weekly_commits(directory: Path) -> list[tuple[str, str]]:
    """Get one commit per week from the repo's history.

    Returns list of (date_str, commit_hash) tuples.
    """
    first_date = get_first_commit_date(directory)
    now = datetime.now(tz=datetime.UTC)

    weeks: list[tuple[str, str]] = []
    current = first_date
    while current <= now:
        iso = current.strftime("%Y-%m-%dT%H:%M:%S%z")
        if not iso:
            iso = current.isoformat()
        result = _git("rev-list", "-1", f"--before={iso}", "HEAD", cwd=directory)
        if result.returncode == 0 and result.stdout.strip():
            commit = result.stdout.strip()
            date_str = current.strftime("%Y-%m-%d")
            if not weeks or weeks[-1][1] != commit:
                weeks.append((date_str, commit))
        current += timedelta(weeks=1)

    # Always include the latest commit
    result = _git("rev-parse", "HEAD", cwd=directory)
    if result.returncode == 0:
        head = result.stdout.strip()
        if not weeks or weeks[-1][1] != head:
            weeks.append((now.strftime("%Y-%m-%d"), head))

    return weeks


def count_lines_at_commit(directory: Path, commit: str) -> dict[str, int]:
    """List files and count lines at a specific commit using git show."""
    result = _git("ls-tree", "-r", "--name-only", commit, cwd=directory)
    if result.returncode != 0:
        return {}

    counts: dict[str, int] = defaultdict(int)
    for filepath in result.stdout.splitlines():
        ext = Path(filepath).suffix or "(no extension)"
        if ext in BINARY_EXTENSIONS:
            continue
        blob = _git("show", f"{commit}:{filepath}", cwd=directory)
        if blob.returncode != 0:
            continue
        counts[ext] += blob.stdout.count("\n")
    return dict(counts)


@app.command()
def snapshot(
    directory: Annotated[Path, typer.Argument(help="Directory to scan")],
    include_gitignored: Annotated[bool, typer.Option(help="Include files ignored by git")] = False,
) -> None:
    """Count lines of code at the current state of the directory."""
    target = directory.resolve()
    if not target.is_dir():
        raise typer.BadParameter(f"Not a directory: {target}")

    respect_gitignore = not include_gitignored
    print(f"Scanning {target}")
    if respect_gitignore:
        print("Respecting .gitignore (use --include-gitignored to include all files)")
    print()

    counts = count_lines(target, respect_gitignore=respect_gitignore)

    if not counts:
        print("No files found.")
        return

    print(f"{'Extension':<20} {'Lines':>10}")
    print("-" * 32)
    for ext, lines in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{ext:<20} {lines:>10,}")
    print("-" * 32)
    print(f"{'TOTAL':<20} {sum(counts.values()):>10,}")


@app.command()
def history(
    directory: Annotated[Path, typer.Argument(help="Git repo directory to scan")],
) -> None:
    """Walk through git history in 1-week increments, counting lines at each point."""
    target = directory.resolve()
    if not target.is_dir():
        raise typer.BadParameter(f"Not a directory: {target}")

    weeks = get_weekly_commits(target)
    if not weeks:
        print("No commits found.")
        return

    print(f"Scanning {len(weeks)} weekly snapshots in {target}\n")

    all_extensions: set[str] = set()
    weekly_data: list[tuple[str, dict[str, int]]] = []

    for date_str, commit in weeks:
        print(f"  Processing {date_str} ({commit[:8]})...")
        counts = count_lines_at_commit(target, commit)
        all_extensions.update(counts.keys())
        weekly_data.append((date_str, counts))

    # Sort extensions by total lines across all weeks
    ext_totals = defaultdict(int)
    for _, counts in weekly_data:
        for ext, lines in counts.items():
            ext_totals[ext] += lines
    sorted_exts = sorted(ext_totals, key=lambda e: ext_totals[e], reverse=True)

    # Print table
    top_exts = sorted_exts[:MAX_DISPLAY_EXTENSIONS]
    header = f"{'Date':<12}" + "".join(f"{ext:>10}" for ext in top_exts) + f"{'TOTAL':>10}"
    print(f"\n{header}")
    print("-" * len(header))

    for date_str, counts in weekly_data:
        row = f"{date_str:<12}"
        for ext in top_exts:
            row += f"{counts.get(ext, 0):>10,}"
        row += f"{sum(counts.values()):>10,}"
        print(row)

    remaining = len(sorted_exts) - MAX_DISPLAY_EXTENSIONS
    if remaining > 0:
        typer.echo(f"\n({remaining} more extensions not shown)")


if __name__ == "__main__":
    app()
