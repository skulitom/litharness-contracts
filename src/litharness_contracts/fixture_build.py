"""Build golden fixture artifacts from fixtures/source definitions.

Prose lives in per-scene .md files; annotations live in def.json and cite
evidence as ``{"scene": ..., "quote": ...}``. This builder locates each quote
(which must occur exactly once in its scene), computes exact offsets and
SHA-256 hashes, and assembles typed contract artifacts. All IDs are
deterministic (UUIDv5) and timestamps are fixed, so rebuilding from identical
sources is byte-stable — the drift test depends on this.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from ._serde import SCHEMA_VERSION, to_jsonable
from .context import ContextOperation, ContextQuery
from .envelope import ArtifactMeta, ToolIdentity
from .evaluation import (
    ConfidenceBasis,
    EvaluationArtifact,
    Finding,
    FindingCategory,
    FindingScope,
    FindingStatus,
    Reproduction,
    Severity,
    SuggestedAction,
)
from .goldens import (
    GoldContextCase,
    GoldContextSuite,
    GoldContextTarget,
    GoldImpactCase,
    GoldImpactExpectation,
    GoldImpactSuite,
    ImpactLabel,
)
from .ids import EvidenceSpan, ResourceKind, ResourceRef, StoryPosition
from .manuscript import ManuscriptNode, ManuscriptRevision, NodeKind
from .plans import PlanAuthority, PlanItem, PlanKind, PlanSnapshot
from .propagation import (
    ChangeActor,
    ChangeOperation,
    ChangeOpKind,
    ChangeSet,
    ExtractedChange,
    ExtractedChangeKind,
)
from .state import StateAuthority, StateRecord, StateRecordKind, StateSnapshot

FIXED_CREATED_AT = "2026-08-12T00:00:00Z"
BUILDER_TOOL = ToolIdentity(name="litharness-contracts-fixtures", version="0.1.0")

_RECORD_KIND_TO_RESOURCE = {
    StateRecordKind.ASSERTION: ResourceKind.ASSERTION,
    StateRecordKind.EVENT: ResourceKind.STATE_EVENT,
    StateRecordKind.RELATIONSHIP: ResourceKind.RELATIONSHIP,
    StateRecordKind.KNOWLEDGE: ResourceKind.KNOWLEDGE,
    StateRecordKind.THREAD: ResourceKind.THREAD,
    StateRecordKind.WORLD_RULE: ResourceKind.WORLD_RULE,
}


def det_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "litharness://" + "/".join(parts)))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class FixtureError(ValueError):
    pass


class FixtureBuilder:
    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)
        self.spec = json.loads((self.source_dir / "def.json").read_text(encoding="utf-8"))
        self.fixture_id: str = self.spec["fixture_id"]
        self.project_id = det_id(self.fixture_id, "project")
        self.book_id = det_id(self.fixture_id, "book")
        self.branch_id = det_id(self.fixture_id, "branch", "main")
        self.revision_id = det_id(self.fixture_id, "revision", "r1")
        self.scene_text: dict[str, str] = {}
        self.scene_version: dict[str, str] = {}
        for scene in self.spec["scenes"]:
            text = (self.source_dir / scene["file"]).read_text(encoding="utf-8").replace("\r\n", "\n")
            self.scene_text[scene["id"]] = text
            self.scene_version[scene["id"]] = det_id(self.fixture_id, scene["id"], sha256_text(text))
        self._record_kinds: dict[str, StateRecordKind] = {
            r["id"]: StateRecordKind(r["kind"]) for r in self.spec["state_records"]
        }
        self._plan_ids = {p["id"] for p in self.spec["plans"]}
        self._finding_ids = {f["id"] for f in self.spec["gold_findings"]}
        self._derived = set(self.spec.get("derived_nodes", []))
        self._query_ids = {q["id"] for q in self.spec.get("context_gold", [])}

    # ---- reference helpers -------------------------------------------------

    def _ref(self, logical_id: str, kind: ResourceKind, version_id: str | None = None) -> ResourceRef:
        return ResourceRef(
            project_id=self.project_id,
            book_id=self.book_id,
            branch_id=self.branch_id,
            logical_id=logical_id,
            kind=kind,
            version_id=version_id,
        )

    def scene_ref(self, scene_id: str) -> ResourceRef:
        return self._ref(scene_id, ResourceKind.MANUSCRIPT_SCENE, self.scene_version[scene_id])

    def resolve_target(self, target_id: str) -> ResourceRef:
        if target_id == "book":
            return self._ref("book", ResourceKind.MANUSCRIPT_BOOK, self.revision_id)
        if target_id in self.scene_text:
            return self.scene_ref(target_id)
        if target_id in self._record_kinds:
            return self._ref(target_id, _RECORD_KIND_TO_RESOURCE[self._record_kinds[target_id]])
        if target_id in self._plan_ids:
            return self._ref(target_id, ResourceKind.PLAN)
        if target_id in self._finding_ids:
            return self._ref(target_id, ResourceKind.FINDING)
        if target_id in self._derived:
            return self._ref(target_id, ResourceKind.SUMMARY)
        if target_id in self._query_ids:
            return self._ref(target_id, ResourceKind.CONTEXT_PACKET)
        if target_id.startswith("entity:"):
            return self._ref(target_id, ResourceKind.ENTITY)
        raise FixtureError(f"{self.fixture_id}: cannot resolve target id {target_id!r}")

    def span(self, scene_id: str, quote: str) -> EvidenceSpan:
        if scene_id not in self.scene_text:
            raise FixtureError(f"{self.fixture_id}: unknown scene {scene_id!r}")
        text = self.scene_text[scene_id]
        count = text.count(quote)
        if count != 1:
            raise FixtureError(
                f"{self.fixture_id}/{scene_id}: quote occurs {count} times (must be exactly 1): {quote!r}"
            )
        start = text.index(quote)
        return EvidenceSpan(
            source=self.scene_ref(scene_id),
            start=start,
            end=start + len(quote),
            content_sha256=sha256_text(quote),
        )

    def _spans(self, items: list[dict]) -> list[EvidenceSpan]:
        return [self.span(item["scene"], item["quote"]) for item in items]

    def _meta(self, artifact_kind: str, name: str) -> ArtifactMeta:
        return ArtifactMeta(
            schema_version=SCHEMA_VERSION,
            artifact_id=det_id(self.fixture_id, artifact_kind, name),
            artifact_kind=artifact_kind,
            created_at=FIXED_CREATED_AT,
            actor="fixture-builder",
            tool=BUILDER_TOOL,
            source_revisions=[self._ref("book", ResourceKind.MANUSCRIPT_BOOK, self.revision_id)],
        )

    # ---- artifact builders -------------------------------------------------

    def manuscript(self) -> ManuscriptRevision:
        nodes = [
            ManuscriptNode(
                logical_id="book",
                kind=NodeKind.BOOK,
                position_key="000",
                title=self.spec["book_title"],
                version_id=self.revision_id,
            )
        ]
        for i, scene in enumerate(self.spec["scenes"], start=1):
            text = self.scene_text[scene["id"]]
            nodes.append(
                ManuscriptNode(
                    logical_id=scene["id"],
                    kind=NodeKind.SCENE,
                    position_key=f"{i * 10:03d}",
                    parent_logical_id="book",
                    title=scene["title"],
                    content=text,
                    content_sha256=sha256_text(text),
                    version_id=self.scene_version[scene["id"]],
                )
            )
        return ManuscriptRevision(
            meta=self._meta("manuscript_revision", "r1"),
            book_id=self.book_id,
            branch_id=self.branch_id,
            revision_id=self.revision_id,
            nodes=nodes,
        )

    def plans(self) -> PlanSnapshot:
        items = [
            PlanItem(
                logical_id=p["id"],
                kind=PlanKind(p["kind"]),
                text=p["text"],
                authority=PlanAuthority(p["authority"]),
                locked=bool(p.get("locked", False)),
            )
            for p in self.spec["plans"]
        ]
        return PlanSnapshot(
            meta=self._meta("plan_snapshot", "r1"),
            book_id=self.book_id,
            branch_id=self.branch_id,
            revision_id=self.revision_id,
            items=items,
        )

    def state(self) -> StateSnapshot:
        records = []
        for r in self.spec["state_records"]:
            records.append(
                StateRecord(
                    record_id=r["id"],
                    kind=StateRecordKind(r["kind"]),
                    subject=r["subject"],
                    predicate=r["predicate"],
                    value=r.get("value"),
                    story_position=StoryPosition(order_key=r["position"]),
                    authority=StateAuthority(r["authority"]),
                    pov_visibility=list(r.get("pov_visibility", [])),
                    evidence=self._spans(r.get("evidence", [])),
                    note=r.get("note"),
                    predicate_registry_version="fixture.v1",
                )
            )
        return StateSnapshot(
            meta=self._meta("state_snapshot", "r1"),
            book_id=self.book_id,
            branch_id=self.branch_id,
            revision_id=self.revision_id,
            records=records,
        )

    def findings(self) -> EvaluationArtifact:
        findings = []
        for f in self.spec["gold_findings"]:
            scene_ids = sorted(
                {f["primary"]["scene"], *(s["scene"] for s in f.get("supporting", []))}
            )
            findings.append(
                Finding(
                    finding_id=f["id"],
                    category=FindingCategory(f["category"]),
                    status=FindingStatus(f["status"]),
                    scope=FindingScope(book_id=self.book_id, scene_ids=scene_ids),
                    severity=Severity(f["severity"]),
                    message=f["message"],
                    evaluation_run_id="gold",
                    subtype=f.get("subtype"),
                    primary_span=self.span(f["primary"]["scene"], f["primary"]["quote"]),
                    supporting_evidence=self._spans(f.get("supporting", [])),
                    rule_or_critic_id=f.get("rule_id"),
                    confidence=1.0,
                    confidence_basis=ConfidenceBasis.DETERMINISTIC,
                    evidence_confidence=1.0,
                    claim=dict(f.get("claim", {})),
                    reproduction=Reproduction(config_hash="fixture", policy_version="gold.v1"),
                    dependencies=[self.resolve_target(d) for d in f.get("dependencies", [])],
                    suggested_action=(
                        SuggestedAction.DISMISS
                        if f["status"] == "accepted_intentional"
                        else SuggestedAction.INSPECT
                    ),
                )
            )
        return EvaluationArtifact(
            meta=self._meta("evaluation_artifact", "gold"),
            run_id="gold",
            plan_id="gold-annotations",
            findings=findings,
        )

    def context_gold(self) -> GoldContextSuite:
        cases = []
        for q in self.spec.get("context_gold", []):
            query = ContextQuery(
                meta=self._meta("context_query", q["id"]),
                query_id=q["id"],
                operation=ContextOperation(q["operation"]),
                target=self.resolve_target(q["target"]),
                token_budget=int(q["token_budget"]),
                pov_character_id=q.get("pov"),
                intent=q.get("intent"),
                policy_version="gold.v1",
            )
            cases.append(
                GoldContextCase(
                    query=query,
                    mandatory=[self._context_target(t) for t in q.get("mandatory", [])],
                    forbidden=[self._context_target(t) for t in q.get("forbidden", [])],
                    notes=q.get("notes"),
                )
            )
        return GoldContextSuite(
            meta=self._meta("gold_context_suite", "r1"),
            fixture_id=self.fixture_id,
            cases=cases,
        )

    def _context_target(self, t: dict) -> GoldContextTarget:
        if "quote" in t:
            return GoldContextTarget(reason=t["reason"], span=self.span(t["scene"], t["quote"]))
        if "record" in t:
            return GoldContextTarget(reason=t["reason"], ref=self.resolve_target(t["record"]))
        if "plan" in t:
            return GoldContextTarget(reason=t["reason"], ref=self.resolve_target(t["plan"]))
        raise FixtureError(f"{self.fixture_id}: context target needs quote/record/plan: {t!r}")

    def impact_gold(self) -> GoldImpactSuite:
        cases = []
        for scenario in self.spec.get("impact_gold", []):
            operations = []
            for op in scenario["operations"]:
                kind = ChangeOpKind(op["kind"])
                if "quote" in op:
                    span = self.span(op["scene"], op["quote"])  # validates existence
                    operations.append(
                        ChangeOperation(
                            kind=kind,
                            logical_source_id=op["scene"],
                            before_version=self.scene_version[op["scene"]],
                            after_version=det_id(self.fixture_id, scenario["id"], op["scene"], "after"),
                            before_hash=span.content_sha256,
                            after_hash=sha256_text(op["new_text"]) if "new_text" in op else None,
                            detail={"quote": op["quote"], "new_text": op.get("new_text")},
                        )
                    )
                elif "anchor_quote" in op:
                    self.span(op["scene"], op["anchor_quote"])  # validates existence
                    operations.append(
                        ChangeOperation(
                            kind=kind,
                            logical_source_id=op["scene"],
                            before_version=self.scene_version[op["scene"]],
                            after_version=det_id(self.fixture_id, scenario["id"], op["scene"], "after"),
                            detail={"anchor_quote": op["anchor_quote"], "new_text": op.get("new_text")},
                        )
                    )
                else:
                    operations.append(
                        ChangeOperation(
                            kind=kind,
                            logical_source_id=f"entity:{op['entity']}" if "entity" in op else op.get("scene", "book"),
                            detail=dict(op.get("detail", {})),
                        )
                    )
            extracted = [
                ExtractedChange(
                    kind=ExtractedChangeKind(c["kind"]),
                    subject=c.get("subject"),
                    predicate=c.get("predicate"),
                    before=c.get("before"),
                    after=c.get("after"),
                    confidence=1.0,
                )
                for c in scenario.get("extracted_changes", [])
            ]
            change_set = ChangeSet(
                meta=self._meta("change_set", scenario["id"]),
                change_set_id=det_id(self.fixture_id, "change_set", scenario["id"]),
                base_revision=self.revision_id,
                target_branch=self.branch_id,
                actor=ChangeActor.AUTHOR,
                operations=operations,
                idempotency_key=det_id(self.fixture_id, "idempotency", scenario["id"]),
                extracted_changes=extracted,
                declared_intent=scenario.get("declared_intent"),
            )
            expected = [
                GoldImpactExpectation(
                    target=self.resolve_target(e["target"]),
                    label=ImpactLabel(e["label"]),
                    note=e.get("note"),
                )
                for e in scenario["expected"]
            ]
            cases.append(
                GoldImpactCase(
                    scenario_id=scenario["id"],
                    description=scenario["description"],
                    change_set=change_set,
                    expected=expected,
                )
            )
        return GoldImpactSuite(
            meta=self._meta("gold_impact_suite", "r1"),
            fixture_id=self.fixture_id,
            cases=cases,
        )

    # ---- entry point -------------------------------------------------------

    def build(self) -> dict[str, Any]:
        """Return {golden filename: jsonable payload}."""
        return {
            "manuscript.json": to_jsonable(self.manuscript()),
            "plans.json": to_jsonable(self.plans()),
            "state.json": to_jsonable(self.state()),
            "findings.json": to_jsonable(self.findings()),
            "context_gold.json": to_jsonable(self.context_gold()),
            "impact_gold.json": to_jsonable(self.impact_gold()),
        }


def build_fixture(source_dir: Path) -> dict[str, Any]:
    return FixtureBuilder(source_dir).build()


def render_golden(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
