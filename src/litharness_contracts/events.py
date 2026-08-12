"""Event envelope and the core event vocabulary (LitHarness PLAN section 13.3).

Delivery is at-least-once; consumers are idempotent and tolerate replay and
out-of-order arrival using expected versions.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class EventType(str, enum.Enum):
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
