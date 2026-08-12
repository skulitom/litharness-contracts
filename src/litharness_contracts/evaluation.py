"""Evaluation contracts (mirrors ContinuityEvaluation PLAN section 5).

A ``Finding`` is a value object that travels inside an ``EvaluationArtifact``
envelope. Finding invariants (enforced by consumers and fixture tests, not by
the type system): severity and confidence are independent; a finding must
have at least one resolvable source reference unless its status is
``evaluation_error``; findings never contain an automatically accepted prose
replacement.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from .envelope import ArtifactMeta, ModelIdentifier
from .ids import EvidenceSpan, ResourceRef


class FindingCategory(str, enum.Enum):
    TIMELINE = "timeline"
    KNOWLEDGE = "knowledge"
    PHYSICAL_STATE = "physical_state"
    INVENTORY = "inventory"
    RELATIONSHIP = "relationship"
    LOCATION = "location"
    CAUSALITY = "causality"
    PROMISE_PAYOFF = "promise_payoff"
    WORLD_RULE = "world_rule"
    STYLE = "style"
    REPETITION = "repetition"
    PACING = "pacing"
    UNKNOWN = "unknown"


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    ACCEPTED_INTENTIONAL = "accepted_intentional"
    CONFIRMED = "confirmed"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"
    EVALUATION_ERROR = "evaluation_error"
    UNKNOWN = "unknown"


class Severity(str, enum.Enum):
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ConfidenceBasis(str, enum.Enum):
    DETERMINISTIC = "deterministic"
    CALIBRATED_MODEL = "calibrated_model"
    ENSEMBLE = "ensemble"
    HEURISTIC = "heuristic"
    UNKNOWN = "unknown"


class SuggestedAction(str, enum.Enum):
    INSPECT = "inspect"
    UPDATE_STATE = "update_state"
    REPAIR_SPAN = "repair_span"
    REVISE_PLAN = "revise_plan"
    DISMISS = "dismiss"
    UNKNOWN = "unknown"


@dataclass
class FindingScope:
    book_id: str
    chapter_ids: list[str] = field(default_factory=list)
    scene_ids: list[str] = field(default_factory=list)


@dataclass
class Reproduction:
    config_hash: str | None = None
    policy_version: str | None = None
    model_digest: str | None = None


@dataclass
class Finding:
    finding_id: str
    category: FindingCategory
    status: FindingStatus
    scope: FindingScope
    severity: Severity
    message: str
    evaluation_run_id: str | None = None
    subtype: str | None = None
    primary_span: EvidenceSpan | None = None
    supporting_evidence: list[EvidenceSpan] = field(default_factory=list)
    contradicting_evidence: list[EvidenceSpan] = field(default_factory=list)
    rule_or_critic_id: str | None = None
    severity_rationale: str | None = None
    confidence: float | None = None
    confidence_basis: ConfidenceBasis = ConfidenceBasis.UNKNOWN
    evidence_confidence: float | None = None
    claim: dict[str, Any] = field(default_factory=dict)
    reproduction: Reproduction | None = None
    dependencies: list[ResourceRef] = field(default_factory=list)
    suggested_action: SuggestedAction = SuggestedAction.INSPECT


@dataclass
class DetectorSpec:
    detector_id: str
    version: str


@dataclass
class CriticSpec:
    critic_id: str
    model: ModelIdentifier | None = None


@dataclass
class EvaluationPlan:
    meta: ArtifactMeta
    plan_id: str
    manuscript_revision: ResourceRef
    detectors: list[DetectorSpec]
    state_snapshot: ResourceRef | None = None
    context_packet_id: str | None = None
    critics: list[CriticSpec] = field(default_factory=list)
    categories: list[FindingCategory] = field(default_factory=list)
    thresholds_profile: str | None = None
    seed: int | None = None


@dataclass
class EvaluationError:
    stage: str
    reason: str
    detail: str | None = None


@dataclass
class EvaluationArtifact:
    meta: ArtifactMeta
    run_id: str
    plan_id: str
    findings: list[Finding]
    errors: list[EvaluationError] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
