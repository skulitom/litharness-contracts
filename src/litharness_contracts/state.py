"""World-state contracts.

Shapes are aligned with BookWorldState's domain (temporal, provenance-aware,
branch-scoped records; candidates reviewed before acceptance). BookWorldState
remains authoritative for state semantics; these contracts are the neutral
interchange shape. No proposal becomes canon merely because a model returned
it (LitHarness PLAN section 9.2).

``pov_visibility``: empty list means objective/public state; a non-empty list
names the characters who hold this knowledge or belief.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from .envelope import ArtifactMeta
from .ids import EvidenceSpan, ResourceRef, StoryPosition


class StateRecordKind(str, enum.Enum):
    ASSERTION = "assertion"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    KNOWLEDGE = "knowledge"
    THREAD = "thread"
    WORLD_RULE = "world_rule"
    UNKNOWN = "unknown"


class StateAuthority(str, enum.Enum):
    AUTHOR_LOCKED = "author_locked"
    ACCEPTED_CANON = "accepted_canon"
    DERIVED = "derived"
    PROPOSED = "proposed"
    UNKNOWN = "unknown"


@dataclass
class StateRecord:
    record_id: str
    kind: StateRecordKind
    subject: str
    predicate: str
    value: Any = None
    object_ref: str | None = None
    story_position: StoryPosition | None = None
    authority: StateAuthority = StateAuthority.PROPOSED
    pov_visibility: list[str] = field(default_factory=list)
    evidence: list[EvidenceSpan] = field(default_factory=list)
    confidence: float | None = None
    predicate_registry_version: str | None = None
    note: str | None = None


@dataclass
class StateSnapshot:
    meta: ArtifactMeta
    book_id: str
    branch_id: str
    revision_id: str
    records: list[StateRecord]
    as_of: StoryPosition | None = None


class CandidateStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass
class StateCandidate:
    candidate_id: str
    record: StateRecord
    extraction_source: ResourceRef | None = None
    rationale: str | None = None
    status: CandidateStatus = CandidateStatus.PROPOSED


@dataclass
class StateCandidateBatch:
    meta: ArtifactMeta
    book_id: str
    branch_id: str
    base_revision_id: str
    candidates: list[StateCandidate]
    idempotency_key: str
    expected_base_version: str | None = None
