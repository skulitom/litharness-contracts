"""Event envelope and the core event vocabulary (LitHarness PLAN section 13.3).

Delivery is at-least-once; consumers are idempotent and tolerate replay and
out-of-order arrival using expected versions.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class EventType(str, enum.Enum):
    """Named event types.

    Unrecognized values decode to ``UNKNOWN`` rather than failing, so adding a member is
    additive for *readers*. It is not additive for *writers*: construction goes through
    ``EventType(value)`` and raises on an unknown string, so a producer cannot emit an
    event this enum does not carry. That asymmetry is why the Conductor block below had to
    land before LitHarness could record a directive or a policy decision at all — those
    events were unrepresentable, not merely unnamed.
    """

    PLAN_CHANGED = "PlanChanged"
    MANUSCRIPT_CANDIDATE_CREATED = "ManuscriptCandidateCreated"
    MANUSCRIPT_REVISION_ACCEPTED = "ManuscriptRevisionAccepted"
    STATE_CANDIDATES_EXTRACTED = "StateCandidatesExtracted"
    STATE_RECORDS_ACCEPTED = "StateRecordsAccepted"
    CONTEXT_PACKET_CREATED = "ContextPacketCreated"
    EVALUATION_COMPLETED = "EvaluationCompleted"
    FINDING_STATUS_CHANGED = "FindingStatusChanged"
    IMPACT_ANALYZED = "ImpactAnalyzed"
    REVISION_PLAN_APPROVED = "RevisionPlanApproved"
    ARTIFACT_INVALIDATED = "ArtifactInvalidated"
    ARTIFACT_RECOMPUTED = "ArtifactRecomputed"
    EXPORT_CREATED = "ExportCreated"
    JOB_FAILED = "JobFailed"

    # -- Conductor events (1.1). LitHarness PLAN.md sections 4.1-4.3. ----------------
    #: A tick completed, with its outcome and what it reconciled.
    TICK_COMPLETED = "TickCompleted"
    #: A director directive was durably captured. Interpreting it is a separate concern,
    #: because capture must not wait on a planner existing to read it.
    DIRECTIVE_INGESTED = "DirectiveIngested"
    #: An acceptance-policy verdict was recorded — the gate ladder's audit trail.
    POLICY_DECISION_RECORDED = "PolicyDecisionRecorded"
    #: Policy could not resolve a unit of work; it is parked and queued for a human.
    EXCEPTION_RAISED = "ExceptionRaised"
    #: An exception was closed by a director decision.
    EXCEPTION_RESOLVED = "ExceptionResolved"
    #: A digest was published for a period.
    DIGEST_PUBLISHED = "DigestPublished"
    #: A provider call fell back off its first choice. Never silent: a fallback changes an
    #: artifact's provenance and may invalidate a reproducibility claim.
    PROVIDER_FELL_BACK = "ProviderFellBack"
    #: A budget ceiling was reached and work was throttled or parked.
    BUDGET_EXHAUSTED = "BudgetExhausted"

    UNKNOWN = "unknown"


@dataclass
class EventEnvelope:
    schema_version: str
    event_id: str
    event_type: EventType
    created_at: str
    actor: str
    project_id: str
    idempotency_key: str
    book_id: str | None = None
    branch_id: str | None = None
    revision_id: str | None = None
    causation_id: str | None = None
    correlation_id: str | None = None
    expected_version: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    payload_digest: str | None = None
