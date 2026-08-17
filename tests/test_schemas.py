"""Committed schemas match the dataclasses; goldens validate against them."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import litharness_contracts as lc
from litharness_contracts._schema import render_schema
from litharness_contracts.fixtures import golden_root

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"

GOLDEN_TYPE_BY_FILE = {
    "manuscript.json": lc.ManuscriptRevision,
    "plans.json": lc.PlanSnapshot,
    "state.json": lc.StateSnapshot,
    "findings.json": lc.EvaluationArtifact,
    "context_gold.json": lc.GoldContextSuite,
    "impact_gold.json": lc.GoldImpactSuite,
}

GOLDEN_SCHEMA_BY_FILE = {
    "manuscript.json": "manuscript_revision",
    "plans.json": "plan_snapshot",
    "state.json": "state_snapshot",
    "findings.json": "evaluation_artifact",
    "context_gold.json": "gold_context_suite",
    "impact_gold.json": "gold_impact_suite",
}


@pytest.mark.parametrize("name", sorted(lc.ALL_SCHEMA_TYPES))
def test_committed_schema_matches_generated(name: str) -> None:
    cls = lc.ALL_SCHEMA_TYPES[name]
    schema_id = f"https://litharness.dev/schemas/{name}.schema.json"
    expected = render_schema(cls, schema_id)
    path = SCHEMA_DIR / f"{name}.schema.json"
    assert path.exists(), f"missing committed schema {path.name}; run tools/generate_schemas.py"
    committed = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert committed == expected, f"{path.name} drifted; run tools/generate_schemas.py"


def _golden_files() -> list[Path]:
    return sorted(golden_root().glob("*/*.json"))


@pytest.mark.parametrize("path", _golden_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_golden_validates_against_schema(path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema_name = GOLDEN_SCHEMA_BY_FILE[path.name]
    schema = json.loads((SCHEMA_DIR / f"{schema_name}.schema.json").read_text(encoding="utf-8"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(payload, schema)


@pytest.mark.parametrize("path", _golden_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_golden_parses_as_contract_type(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    artifact = lc.parse_artifact(GOLDEN_TYPE_BY_FILE[path.name], payload)
    assert lc.to_jsonable(artifact) == payload
