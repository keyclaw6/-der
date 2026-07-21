#!/usr/bin/env python3
"""Apply a human-approved OpenSpec change and keep Git as the only archive."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGES = ROOT / "openspec" / "changes"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("slug", help="active change directory name")
    result.add_argument(
        "--human-approved",
        action="store_true",
        help="acknowledge that a human reviewed this exact change",
    )
    return result


def openspec_binary() -> str:
    found = shutil.which("openspec")
    if found:
        return found
    local = ROOT / "node_modules" / ".bin" / ("openspec.cmd" if sys.platform == "win32" else "openspec")
    if local.is_file():
        return str(local)
    raise RuntimeError("OpenSpec is not installed; run `npm ci`")


def main() -> int:
    args = parser().parse_args()
    if not args.human_approved:
        print("ERROR: --human-approved is required", file=sys.stderr)
        return 2
    if not SLUG.fullmatch(args.slug):
        print("ERROR: slug must be kebab-case", file=sys.stderr)
        return 2

    active = CHANGES / args.slug
    if not active.is_dir():
        print(f"ERROR: active change not found: {active.relative_to(ROOT)}", file=sys.stderr)
        return 1

    try:
        subprocess.run(
            [openspec_binary(), "archive", args.slug, "--yes"],
            cwd=ROOT,
            check=True,
        )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    archive_root = CHANGES / "archive"
    if archive_root.is_dir():
        matches = list(archive_root.glob(f"*-{args.slug}"))
        for path in matches:
            shutil.rmtree(path)
        if not any(archive_root.iterdir()):
            archive_root.rmdir()

    ownership = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "spec_owners.py")],
        cwd=ROOT,
        check=False,
    )
    if ownership.returncode != 0:
        return ownership.returncode

    print(
        "Change finalized. Commit the baseline spec updates, ownership updates, "
        "and active-change deletion together."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
