#!/usr/bin/env python3
"""Run small repository-wide invariants that are independent of project stack."""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print(
        "ERROR: Python 3.11 or newer is required to run repository checks "
        f"(tomllib became stdlib in 3.11); found {sys.version.split()[0]}. "
        "Install Python 3.11+ and re-run `npm run check`.",
        file=sys.stderr,
    )
    raise SystemExit(1)

import re
import subprocess
from pathlib import Path

from spec_owners import validate as validate_ownership

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ASSIGNMENT = re.compile(
    r"^\s*(?:export\s+)?DOTENV_PRIVATE_KEY(?:_[A-Z0-9_]+)?\s*=",
    re.MULTILINE,
)


def git_files(*args: str) -> list[Path] | None:
    """List repository files via `git ls-files`, or None when git is unavailable."""
    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return None
    result = subprocess.run(
        ["git", "ls-files", "-z", *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    errors: list[str] = []

    present = git_files("--cached", "--others", "--exclude-standard")
    if present is None:
        generated = {
            ".git",
            "node_modules",
            ".codebase-memory",
            "__pycache__",
            "coverage",
            "dist",
            "build",
        }
        present = [
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and not (generated & set(path.relative_to(ROOT).parts[:-1]))
        ]

    agents = sorted(
        path.relative_to(ROOT).as_posix()
        for path in present
        if path.is_file() and path.name.lower() == "agents.md"
    )
    if agents != ["AGENTS.md"]:
        errors.append(
            "the repository must contain exactly one AGENTS.md at the root; "
            f"found: {agents}. Fold nested agent instructions into the root map "
            "and delete the copies."
        )

    for required in ("VISION.md", "openspec/config.yaml", ".env"):
        if not (ROOT / required).is_file():
            errors.append(f"missing required file: {required}")

    for required in ("src", "tests", "openspec/specs", "openspec/changes", "scripts"):
        if not (ROOT / required).is_dir():
            errors.append(f"missing required directory: {required}")

    archive = ROOT / "openspec" / "changes" / "archive"
    if archive.exists():
        errors.append("openspec/changes/archive must not exist; Git is the archive")

    tracked = git_files()
    if tracked is not None:
        for path in tracked:
            relative = path.relative_to(ROOT).as_posix()
            if path.name == ".env.keys" or path.name.startswith(".env.keys."):
                errors.append(f"private dotenvx key file is tracked: {relative}")
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if PRIVATE_ASSIGNMENT.search(text):
                errors.append(
                    f"tracked file contains a dotenvx private-key assignment: {relative}"
                )

        ignored = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", ".env"],
            cwd=ROOT,
            check=False,
        )
        if ignored.returncode == 0:
            errors.append(".env is ignored; encrypted dotenvx files must be tracked")

    errors.extend(validate_ownership())

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Repository checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
