"""Regenerate the golden fixtures from fixtures/source. Run from the repo root:

    uv run python tools/build_fixtures.py

The sources stay outside the package (prose and annotations are authoring input, and the
wheel has no reason to carry them); the generated artifacts are written *inside* it, at
``src/litharness_contracts/fixtures/golden/``, so they ship to consumers.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from litharness_contracts.fixture_build import build_fixture, render_golden  # noqa: E402
from litharness_contracts.fixtures import golden_root as package_golden_root  # noqa: E402


def main() -> None:
    source_root = ROOT / "fixtures" / "source"
    golden_root = package_golden_root()
    for source_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
        outputs = build_fixture(source_dir)
        out_dir = golden_root / source_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for filename, payload in outputs.items():
            path = out_dir / filename
            path.write_text(render_golden(payload), encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
