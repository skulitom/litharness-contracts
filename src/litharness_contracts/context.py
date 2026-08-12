"""Context assembly contracts (mirrors LongRangeContext PLAN sections 5 and 12).

LongRangeContext owns discovery/scoring/packing; consumers receive a frozen
``ContextPacket`` with a consumed-source ledger and explicit omissions.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .envelope import ArtifactMeta
from .ids import EvidenceSpan, ResourceRef, StoryPosition
from .state import StateAuthority


class ContextOperation(str, enum.Enum):
    DRAFT_SCENE = "draft_scene"
    CONTINUE = "continue"
    EVALUATE = "evaluate"
    REPAIR = "repair"
    PLAN = "plan"
    ANSWER = "answer"
    UNKNOWN = "unknown"


class ContextItemKind(str, enum.Enum):
    EXACT_PROSE = "exact_prose"
    PLAN = "plan"
    FACT = "fact"
    EVENT = "event"
    THREAD = "thread"
    SUMMARY = "summary"
    FINDING = "finding"
    AUTHOR_RULE = "author_rule"
    UNKNOWN = "unknown"


@dataclass
class ContextQuery:
    meta: ArtifactMeta
    query_id: str
    operation: ContextOperation
    target: ResourceRef
    token_budget: int
    pov_character_id: str | None = None
    intent: str | None = None
    referenced_entities: list[str] = field(default_factory=list)
    referenced_threads: list[str] = field(default_factory=list)
    story_time_cutoff: StoryPosition | None = None
    hard_requirements: list[ResourceRef] = field(default_factory=list)
    exclusions: list[ResourceRef] = field(default_factory=list)
    model_context_limit: int | None = None
    policy_version: str | None = None


@dataclass
class ContextItem:
    item_id: str
    kind: ContextItemKind
    source: ResourceRef
    text: str
    token_count: int
    authority: StateAuthority = StateAuthority.DERIVED
    confidence: float | None = None
    story_scope: ResourceRef | None = None
    pov_visibility: list[str] = field(default_factory=list)
    provenance: list[EvidenceSpan] = field(default_factory=list)
    dependencies: list[ResourceRef] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class PacketSection:
    name: str
    items: list[ContextItem]


@dataclass
class RejectedCandidate:
    reason: str
    item_id: str | None = None
    source: ResourceRef | None = None


@dataclass
class TokenBudget:
    limit: int
    used: int
    reserved_output: int = 0


@dataclass
class ContextPacket:
    meta: ArtifactMeta
    packet_id: str
    query_id: str
    source_snapshot: ResourceRef
    sections: list[PacketSection]
    budget: TokenBudget
    consumed_sources: list[ResourceRef] = field(default_factory=list)
    rejected_candidates: list[RejectedCandidate] = field(default_factory=list)
