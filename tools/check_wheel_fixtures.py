"""Assert a built wheel actually carries the golden fixtures. Run after `uv build --wheel`:

    uv build --wheel
    uv run --no-project python tools/check_wheel_fixtures.py

This exists because the property consumers depend on is invisible to the test suite. The
suite imports `litharness_contracts` from the source tree, where the fixtures are present no
matter what the build backend is configured to include — so a `[tool.hatch.build]` change
that dropped the data files would leave every test green and publish a wheel whose
`litharness_contracts.fixtures` accessor raises on every call. Opening the archive is the
only check that looks at what is shipped rather than at what is on disk.

Deliberately dependency-free and importable without installing the package (hence the
literal filename list rather than `from litharness_contracts.fixtures import ...`): it runs
against `dist/`, in a job that never syncs the project.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIXTURE_IDS = ("mystery", "litrpg")
GOLDEN_FILENAMES = (
    "manuscript.json",
    "plans.json",
    "state.json",
    "findings.json",
    "context_gold.json",
    "impact_gold.json",
)


def main() -> int:
    wheels = sorted((ROOT / "dist").glob("*.whl"))
    if not wheels:
        print(f"no wheel in {ROOT / 'dist'}; run `uv build --wheel` first", file=sys.stderr)
        return 2
    wheel = wheels[-1]

    expected = {
        f"litharness_contracts/fixtures/golden/{fixture_id}/{filename}"
        for fixture_id in FIXTURE_IDS
        for filename in GOLDEN_FILENAMES
    }
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())

    missing = sorted(expected - members)
    if missing:
        print(f"{wheel.name} is missing {len(missing)} golden artifact(s):", file=sys.stderr)
        for name in missing:
            print(f"  {name}", file=sys.stderr)
        return 1

    print(f"{wheel.name} carries all {len(expected)} golden artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
