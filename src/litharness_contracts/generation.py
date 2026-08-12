"""Generation request/candidate contracts.

Output is always a candidate artifact, never an in-place mutation
(LitHarness PLAN section 10 step 3). All write commands carry idempotency
keys (section 11).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .envelope import ArtifactMeta, ModelIdentifier
from .ids import ResourceRef
from .manuscript import BoundedPatch


class GenerationKind(str, enum.Enum):
    SCENE_DRAFT = "scene_draft"
    CONTINUATION = "continuation"
    REPAIR = "repair"
    STRUCTURED = "structured"
    UNKNOWN = "unknown"


class GenerationStatus(str, enum.Enum):
    COMPLETE = "complete"
    FAILED = "failed"
    REJECTED = "rejected"
    TRUNCATED = "truncated"
    UNKNOWN = "unknown"


@dataclass
class GenerationParams:
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    stop: list[str] = field(default_factory=list)


@dataclass
class GenerationRequest:
    meta: ArtifactMeta
    request_id: str
    kind: GenerationKind
    target: ResourceRef
    model: ModelIdentifier
    idempotency_key: str
    context_packet_id: str | None = None
    params: GenerationParams = field(default_factory=GenerationParams)
    output_schema_id: str | None = None


@dataclass
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass
class ValidationOutcome:
    check: str
    passed: bool
    detail: str | None = None


@dataclass
class GenerationCandidate:
    meta: ArtifactMeta
    candidate_id: str
    request_id: str
    status: GenerationStatus
    content: str | None = None
    patch: BoundedPatch | None = None
    token_usage: TokenUsage | None = None
    validations: list[ValidationOutcome] = field(default_factory=list)
