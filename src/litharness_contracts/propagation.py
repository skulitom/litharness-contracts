"""Change, impact, and revision-plan contracts
(mirrors RevisionPropagation PLAN sections 5, 7, and 10).

A text diff, a semantic delta, and a structured world-state change remain
distinct artifacts. Plans are immutable; execution produces a separate
artifact. Approvals are step-scoped and expire if the base revision changes.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from .envelope import ArtifactMeta
from .ids import EvidenceSpan, ResourceRef


class ChangeActor(str, enum.Enum):
    AUTHOR = "author"
    SYSTEM = "system"
    IMPORT = "import"
    UNKNOWN = "unknown"


class ChangeOpKind(str, enum.Enum):
    REPLACE_SPAN = "replace_span"
    INSERT = "insert"
    DELETE = "delete"
    MOVE = "move"
    RENAME = "rename"
    REORDER = "reorder"
    SPLIT = "split"
    MERGE = "merge"
    UNKNOWN = "unknown"


@dataclass
class ChangeOperation:
    kind: ChangeOpKind
    logical_source_id: str
    before_version: str | None = None
    after_version: str | None = None
    before_hash: str | None = None
    after_hash: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


class ExtractedChangeKind(str, enum.Enum):
    FACT_CHANGED = "fact_changed"
    ENTITY_RENAMED = "entity_renamed"
    EVENT_MOVED = "event_moved"
    EVENT_ADDED = "event_added"
    EVENT_REMOVED = "event_removed"
    PLAN_CHANGED = "plan_changed"
    POV_CHANGED = "pov_changed"
    RULE_CHANGED = "rule_changed"
    SURFACE_ONLY = "surface_only"
    UNKNOWN = "unknown"


@dataclass
class ExtractedChange:
    kind: ExtractedChangeKind
    subject: str | None = None
    predicate: str | None = None
    before: Any = None
    after: Any = None
    evidence: list[EvidenceSpan] = field(default_factory=list)
    confidence: float | None = None


@dataclass
class ChangeSet:
    meta: ArtifactMeta
    change_set_id: str
    base_revision: str
    target_branch: str
    actor: ChangeActor
    operations: list[ChangeOperation]
    idempotency_key: str
    extracted_changes: list[ExtractedChange] = field(default_factory=list)
    declared_intent: str | None = None
    preservation_constraints: list[str] = field(default_factory=list)


class ImpactClass(str, enum.Enum):
    INVALIDATE_RECOMPUTE = "invalidate_recompute"
    STRUCTURED_UPDATE = "structured_update"
    REPAIR_CANDIDATE = "repair_candidate"
    REVIEW_WARNING = "review_warning"
    PRESERVE = "preserve"
    NO_ACTION = "no_action"
    UNKNOWN = "unknown"


@dataclass
class ImpactPathEdge:
    edge_type: str
    from_ref: ResourceRef
    to_ref: ResourceRef
    authority: str | None = None


@dataclass
class ImpactItem:
    target: ResourceRef
    impact_class: ImpactClass
    confidence: float | None = None
    reason: str | None = None
    reason_paths: list[list[ImpactPathEdge]] = field(default_factory=list)


@dataclass
class ImpactReport:
    meta: ArtifactMeta
    report_id: str
    change_set_id: str
    impacts: list[ImpactItem]
    graph_version: str | None = None
    coverage_warnings: list[str] = field(default_factory=list)


class StepAction(str, enum.Enum):
    RECOMPUTE = "recompute"
    PROPOSE_REPAIR = "propose_repair"
    STRUCTURED_UPDATE = "structured_update"
    WARN = "warn"
    NO_OP = "no_op"
    UNKNOWN = "unknown"


class ApprovalMode(str, enum.Enum):
    AUTOMATIC = "automatic"
    REVIEW_AFTER = "review_after"
    AUTHOR_REQUIRED = "author_required"
    NEVER_AUTOMATIC = "never_automatic"
    UNKNOWN = "unknown"


@dataclass
class RevisionStep:
    step_id: str
    target: ResourceRef
    action: StepAction
    approval: ApprovalMode
    reason: str | None = None
    finding_id: str | None = None
    confidence: float | None = None
    preconditions: list[str] = field(default_factory=list)
    preservation_constraints: list[str] = field(default_factory=list)


@dataclass
class RevisionPlan:
    meta: ArtifactMeta
    plan_id: str
    base_revision: str
    change_set_id: str
    steps: list[RevisionStep]
    graph_version: str | None = None
    excluded_candidates: list[ImpactItem] = field(default_factory=list)
    estimated_cost: dict[str, float] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
