#!/usr/bin/env python3
"""Validate ownership for baseline and active OpenSpec requirements."""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print(
        "ERROR: Python 3.11 or newer is required "
        f"(tomllib became stdlib in 3.11); found {sys.version.split()[0]}.",
        file=sys.stderr,
    )
    raise SystemExit(1)

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "openspec" / "specs"
CHANGES = ROOT / "openspec" / "changes"
OWNERSHIP = ROOT / "openspec" / "ownership.toml"
REQUIREMENT = re.compile(r"^### Requirement:\s*(.+?)\s*$")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError(f"cannot derive an identifier from requirement title {value!r}")
    return slug


def requirements_in_file(spec: Path, capability: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line_number, line in enumerate(spec.read_text(encoding="utf-8").splitlines(), 1):
        match = REQUIREMENT.match(line)
        if not match:
            continue
        requirement_id = f"{capability}/{slugify(match.group(1))}"
        location = f"{spec.relative_to(ROOT)}:{line_number}"
        if requirement_id in found:
            raise ValueError(
                f"duplicate requirement id {requirement_id!r}: "
                f"{found[requirement_id]} and {location}"
            )
        found[requirement_id] = location
    return found


def discover_requirements() -> dict[str, str]:
    baseline: dict[str, str] = {}
    for spec in sorted(SPECS.rglob("spec.md")):
        capability = spec.parent.relative_to(SPECS).as_posix()
        for requirement_id, location in requirements_in_file(spec, capability).items():
            if requirement_id in baseline:
                raise ValueError(
                    f"duplicate baseline requirement id {requirement_id!r}: "
                    f"{baseline[requirement_id]} and {location}"
                )
            baseline[requirement_id] = location

    active: dict[str, str] = {}
    for change in sorted(path for path in CHANGES.iterdir() if path.is_dir() and path.name != "archive"):
        change_specs = change / "specs"
        if not change_specs.is_dir():
            continue
        for spec in sorted(change_specs.rglob("spec.md")):
            capability = spec.parent.relative_to(change_specs).as_posix()
            for requirement_id, location in requirements_in_file(spec, capability).items():
                if requirement_id in active:
                    raise ValueError(
                        f"overlapping active requirement id {requirement_id!r}: "
                        f"{active[requirement_id]} and {location}"
                    )
                active[requirement_id] = location

    return baseline | active


def load_ownership() -> dict[str, list[str]]:
    data = tomllib.loads(OWNERSHIP.read_text(encoding="utf-8"))
    raw = data.get("requirements", {})
    if not isinstance(raw, dict):
        raise ValueError("openspec/ownership.toml must contain a [requirements] table")

    owners: dict[str, list[str]] = {}
    for requirement_id, values in raw.items():
        if not isinstance(values, list) or not values or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise ValueError(
                f"ownership entry {requirement_id!r} must be a non-empty list of names"
            )
        owners[requirement_id] = values
    return owners


def validate() -> list[str]:
    errors: list[str] = []
    try:
        requirements = discover_requirements()
        owners = load_ownership()
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, ValueError) as exc:
        return [str(exc)]

    for requirement_id, location in requirements.items():
        if requirement_id not in owners:
            errors.append(f"missing owner for {requirement_id!r} ({location})")

    for requirement_id in owners:
        if requirement_id not in requirements:
            errors.append(f"ownership entry has no baseline or active requirement: {requirement_id!r}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OpenSpec requirement ownership is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
