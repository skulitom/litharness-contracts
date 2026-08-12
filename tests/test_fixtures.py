"""The golden fixtures are internally consistent and rebuild without drift."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import litharness_contracts as lc
from litharness_contracts.fixture_build import build_fixture

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "fixtures" / "source"
GOLDEN_DIR = ROOT / "fixtures" / "golden"

FIXTURES = sorted(p.name for p in SOURCE_DIR.iterdir() if p.is_dir())


def _load_golden(fixture: str, filename: str) -> dict:
    return json.loads((GOLDEN_DIR / fixture / filename).read_text(encoding="utf-8"))


def _scene_texts(fixture: str) -> dict[str, str]:
    manuscript = lc.parse_artifact(lc.ManuscriptRevision, _load_golden(fixture, "manuscript.json"))
    return {n.logical_id: n.content for n in manuscript.nodes if n.content is not None}


def _resolve(span: lc.EvidenceSpan, texts: dict[str, str]) -> str:
    text = texts[span.source.logical_id]
    excerpt = text[span.start : span.end]
    digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    assert digest == span.content_sha256, (
        f"span hash mismatch in {span.source.logical_id}: {excerpt!r}"
    )
    return excerpt


@pytest.mark.parametrize("fixture", FIXTURES)
def test_golden_matches_rebuild(fixture: str) -> None:
    rebuilt = build_fixture(SOURCE_DIR / fixture)
    for filename, payload in rebuilt.items():
        committed = _load_golden(fixture, filename)
        assert committed == payload, (
            f"{fixture}/{filename} drifted from source; run tools/build_fixtures.py"
        )


@pytest.mark.parametrize("fixture", FIXTURES)
def test_every_evidence_span_resolves(fixture: str) -> None:
    texts = _scene_texts(fixture)
    findings = lc.parse_artifact(lc.EvaluationArtifact, _load_golden(fixture, "findings.json"))
    state = lc.parse_artifact(lc.StateSnapshot, _load_golden(fixture, "state.json"))
    for finding in findings.findings:
        assert finding.primary_span is not None
        _resolve(finding.primary_span, texts)
        for span in finding.supporting_evidence:
            _resolve(span, texts)
    for record in state.records:
        for span in record.evidence:
            _resolve(span, texts)


@pytest.mark.parametrize("fixture", FIXTURES)
def test_negative_controls_are_intentional(fixture: str) -> None:
    findings = lc.parse_artifact(lc.EvaluationArtifact, _load_golden(fixture, "findings.json"))
    controls = [f for f in findings.findings if f.finding_id.startswith(("f-control",))]
    assert len(controls) >= 2, "each fixture plants at least two negative controls"
    for control in controls:
        assert control.status is lc.FindingStatus.ACCEPTED_INTENTIONAL
    open_findings = [f for f in findings.findings if f.status is lc.FindingStatus.OPEN]
    assert len(open_findings) >= 6, "each fixture plants at least six genuine defects"


def test_mystery_covers_required_categories() -> None:
    findings = lc.parse_artifact(lc.EvaluationArtifact, _load_golden("mystery", "findings.json"))
    open_categories = {
        f.category for f in findings.findings if f.status is lc.FindingStatus.OPEN
    }
    required = {
        lc.FindingCategory.LOCATION,
        lc.FindingCategory.INVENTORY,
        lc.FindingCategory.PHYSICAL_STATE,
        lc.FindingCategory.KNOWLEDGE,
        lc.FindingCategory.TIMELINE,
        lc.FindingCategory.RELATIONSHIP,
        lc.FindingCategory.PROMISE_PAYOFF,
        lc.FindingCategory.REPETITION,
    }
    assert required <= open_categories


def test_litrpg_numeric_claims_match_status_lines() -> None:
    texts = _scene_texts("litrpg")
    findings = lc.parse_artifact(lc.EvaluationArtifact, _load_golden("litrpg", "findings.json"))
    by_id = {f.finding_id: f for f in findings.findings}

    ledger = by_id["f-gold-ledger"]
    excerpt = _resolve(ledger.primary_span, texts)
    assert f"Gold {ledger.claim['observed']}" in excerpt
    assert ledger.claim["expected"] == 25 - 5

    hp = by_id["f-hp-over-max"]
    excerpt = _resolve(hp.primary_span, texts)
    assert f"HP {hp.claim['observed']}/{hp.claim['max']}" in excerpt
    assert hp.claim["observed"] > hp.claim["max"]

    level = by_id["f-level-regression"]
    excerpt = _resolve(level.primary_span, texts)
    assert f"Level {level.claim['after']}" in excerpt
    assert level.claim["after"] < level.claim["before"]


def test_litrpg_state_ledger_is_annotated_correctly() -> None:
    """The status-snapshot records reproduce exactly what the prose says,
    including the planted defects (which the findings then flag)."""
    state = lc.parse_artifact(lc.StateSnapshot, _load_golden("litrpg", "state.json"))
    snapshots = {
        r.story_position.order_key: r.value
        for r in state.records
        if r.predicate == "status_snapshot"
    }
    assert snapshots["s1"]["gold"] == 45
    assert snapshots["s2"]["gold"] == 45 - 20
    assert snapshots["s3"]["gold"] == 15  # planted: should be 20
    assert snapshots["s4"]["hp"] > snapshots["s4"]["hp_max"]  # planted ceiling break
    assert snapshots["s5"]["level"] < snapshots["s4"]["level"]  # planted regression
    assert snapshots["s6"]["gold"] == 0


@pytest.mark.parametrize("fixture", FIXTURES)
def test_impact_targets_and_ops_resolve(fixture: str) -> None:
    texts = _scene_texts(fixture)
    suite = lc.parse_artifact(lc.GoldImpactSuite, _load_golden(fixture, "impact_gold.json"))
    for case in suite.cases:
        labels = {e.label for e in case.expected}
        assert lc.ImpactLabel.SAFE_PRESERVE in labels, (
            f"{case.scenario_id}: every scenario must pin down what is NOT affected"
        )
        assert case.change_set.idempotency_key
        for op in case.change_set.operations:
            quote = op.detail.get("quote") or op.detail.get("anchor_quote")
            if quote is not None:
                assert texts[op.logical_source_id].count(quote) == 1


@pytest.mark.parametrize("fixture", FIXTURES)
def test_context_gold_targets_resolve(fixture: str) -> None:
    texts = _scene_texts(fixture)
    state = lc.parse_artifact(lc.StateSnapshot, _load_golden(fixture, "state.json"))
    record_ids = {r.record_id for r in state.records}
    suite = lc.parse_artifact(lc.GoldContextSuite, _load_golden(fixture, "context_gold.json"))
    assert suite.cases
    for case in suite.cases:
        assert case.mandatory, f"{case.query.query_id}: needs at least one mandatory target"
        for target in case.mandatory + case.forbidden:
            assert (target.span is None) != (target.ref is None), "exactly one of span/ref"
            if target.span is not None:
                _resolve(target.span, texts)
            elif target.ref is not None and target.ref.kind in (
                lc.ResourceKind.ASSERTION,
                lc.ResourceKind.STATE_EVENT,
                lc.ResourceKind.KNOWLEDGE,
                lc.ResourceKind.THREAD,
                lc.ResourceKind.RELATIONSHIP,
                lc.ResourceKind.WORLD_RULE,
            ):
                assert target.ref.logical_id in record_ids


def test_mystery_pov_trap_exists() -> None:
    """The forbidden-context trap: a record visible only to Brandt must be
    forbidden for the Mara-POV draft query."""
    suite = lc.parse_artifact(lc.GoldContextSuite, _load_golden("mystery", "context_gold.json"))
    draft = next(c for c in suite.cases if c.query.query_id == "q1-draft-scene-6")
    assert draft.query.pov_character_id == "mara"
    forbidden_ids = {t.ref.logical_id for t in draft.forbidden if t.ref is not None}
    assert "rec-brandt-knows-letter" in forbidden_ids

    state = lc.parse_artifact(lc.StateSnapshot, _load_golden("mystery", "state.json"))
    record = next(r for r in state.records if r.record_id == "rec-brandt-knows-letter")
    assert record.pov_visibility == ["brandt"]
    assert record.authority is lc.StateAuthority.AUTHOR_LOCKED
