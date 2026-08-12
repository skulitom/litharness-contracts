"""litharness-contracts: neutral, versioned contracts for the LitHarness program.

Consumers (BookWorldState, LongRangeContext, ContinuityEvaluation,
RevisionPropagation, LitHarness) depend on this package's schemas and golden
fixtures instead of importing each other.
"""

from ._serde import (
    SCHEMA_VERSION,
    ContractError,
    IncompatibleSchemaVersion,
    declared_schema_version,
    from_jsonable,
    parse_artifact,
    schema_major,
    to_jsonable,
)
from .context import (
    ContextItem,
    ContextItemKind,
    ContextOperation,
    ContextPacket,
    ContextQuery,
    PacketSection,
    RejectedCandidate,
    TokenBudget,
)
from .envelope import ArtifactMeta, ModelIdentifier, ToolIdentity
from .evaluation import (
    ConfidenceBasis,
    CriticSpec,
    DetectorSpec,
    EvaluationArtifact,
    EvaluationError,
    EvaluationPlan,
    Finding,
    FindingCategory,
    FindingScope,
    FindingStatus,
    Reproduction,
    Severity,
    SuggestedAction,
)
from .events import EventEnvelope, EventType
from .generation import (
    GenerationCandidate,
    GenerationKind,
    GenerationParams,
    GenerationRequest,
    GenerationStatus,
    TokenUsage,
    ValidationOutcome,
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
from .manuscript import (
    BoundedPatch,
    ManuscriptNode,
    ManuscriptRevision,
    NodeKind,
    PatchOp,
    PatchOpKind,
)
from .plans import PlanAuthority, PlanItem, PlanKind, PlanSnapshot
from .propagation import (
    ApprovalMode,
    ChangeActor,
    ChangeOperation,
    ChangeOpKind,
    ChangeSet,
    ExtractedChange,
    ExtractedChangeKind,
    ImpactClass,
    ImpactItem,
    ImpactPathEdge,
    ImpactReport,
    RevisionPlan,
    RevisionStep,
    StepAction,
)
from .runs import (
    ExportFile,
    ExportFormat,
    ExportManifest,
    InputRef,
    JobRecord,
    JobStatus,
    RunManifest,
)
from .state import (
    CandidateStatus,
    StateAuthority,
    StateCandidate,
    StateCandidateBatch,
    StateRecord,
    StateRecordKind,
    StateSnapshot,
)

# Top-level artifacts: carry an envelope (or, for events, a top-level
# schema_version) and parse through parse_artifact().
ARTIFACT_TYPES: dict[str, type] = {
    "manuscript_revision": ManuscriptRevision,
    "bounded_patch": BoundedPatch,
    "plan_snapshot": PlanSnapshot,
    "state_snapshot": StateSnapshot,
    "state_candidate_batch": StateCandidateBatch,
    "context_query": ContextQuery,
    "context_packet": ContextPacket,
    "generation_request": GenerationRequest,
    "generation_candidate": GenerationCandidate,
    "evaluation_plan": EvaluationPlan,
    "evaluation_artifact": EvaluationArtifact,
    "change_set": ChangeSet,
    "impact_report": ImpactReport,
    "revision_plan": RevisionPlan,
    "run_manifest": RunManifest,
    "job_record": JobRecord,
    "export_manifest": ExportManifest,
    "event_envelope": EventEnvelope,
    "gold_context_suite": GoldContextSuite,
    "gold_impact_suite": GoldImpactSuite,
}

# Value objects that also get standalone schemas because siblings exchange
# them outside a full envelope.
VALUE_TYPES: dict[str, type] = {
    "resource_ref": ResourceRef,
    "evidence_span": EvidenceSpan,
    "finding": Finding,
    "context_item": ContextItem,
    "state_record": StateRecord,
}

ALL_SCHEMA_TYPES: dict[str, type] = {**ARTIFACT_TYPES, **VALUE_TYPES}

# Explicit public surface. Required, not cosmetic: without `__all__` a package
# re-exports nothing under mypy's --no-implicit-reexport (implied by --strict), so
# every consumer that annotates against `lc.Finding` or `lc.ManuscriptRevision`
# fails to type-check at the boundary this package exists to define.


__all__ = [
    "ApprovalMode",
    "ArtifactMeta",
    "BoundedPatch",
    "CandidateStatus",
    "ChangeActor",
    "ChangeOpKind",
    "ChangeOperation",
    "ChangeSet",
    "ConfidenceBasis",
    "ContextItem",
    "ContextItemKind",
    "ContextOperation",
    "ContextPacket",
    "ContextQuery",
    "ContractError",
    "CriticSpec",
    "DetectorSpec",
    "EvaluationArtifact",
    "EvaluationError",
    "EvaluationPlan",
    "EventEnvelope",
    "EventType",
    "EvidenceSpan",
    "ExportFile",
    "ExportFormat",
    "ExportManifest",
    "ExtractedChange",
    "ExtractedChangeKind",
    "Finding",
    "FindingCategory",
    "FindingScope",
    "FindingStatus",
    "GenerationCandidate",
    "GenerationKind",
    "GenerationParams",
    "GenerationRequest",
    "GenerationStatus",
    "GoldContextCase",
    "GoldContextSuite",
    "GoldContextTarget",
    "GoldImpactCase",
    "GoldImpactExpectation",
    "GoldImpactSuite",
    "ImpactClass",
    "ImpactItem",
    "ImpactLabel",
    "ImpactPathEdge",
    "ImpactReport",
    "IncompatibleSchemaVersion",
    "InputRef",
    "JobRecord",
    "JobStatus",
    "ManuscriptNode",
    "ManuscriptRevision",
    "ModelIdentifier",
    "NodeKind",
    "PacketSection",
    "PatchOp",
    "PatchOpKind",
    "PlanAuthority",
    "PlanItem",
    "PlanKind",
    "PlanSnapshot",
    "RejectedCandidate",
    "Reproduction",
    "ResourceKind",
    "ResourceRef",
    "RevisionPlan",
    "RevisionStep",
    "RunManifest",
    "SCHEMA_VERSION",
    "Severity",
    "StateAuthority",
    "StateCandidate",
    "StateCandidateBatch",
    "StateRecord",
    "StateRecordKind",
    "StateSnapshot",
    "StepAction",
    "StoryPosition",
    "SuggestedAction",
    "TokenBudget",
    "TokenUsage",
    "ToolIdentity",
    "ValidationOutcome",
    "declared_schema_version",
    "from_jsonable",
    "parse_artifact",
    "schema_major",
    "to_jsonable",
]
