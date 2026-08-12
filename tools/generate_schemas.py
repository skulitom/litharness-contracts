"""Regenerate schemas/ from the contract dataclasses. Run from the repo root:

    uv run python tools/generate_schemas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from litharness_contracts import ALL_SCHEMA_TYPES  # noqa: E402
from litharness_contracts._schema import render_schema  # noqa: E402


def main() -> None:
    out_dir = ROOT / "schemas"
    out_dir.mkdir(exist_ok=True)
    for name, cls in sorted(ALL_SCHEMA_TYPES.items()):
        schema_id = f"https://litharness.dev/schemas/{name}.schema.json"
        path = out_dir / f"{name}.schema.json"
        path.write_text(render_schema(cls, schema_id), encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
