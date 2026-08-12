"""Conductor artifacts: direction in, decisions and exceptions out (1.1 addition).

LitHarness PLAN.md section 4 decomposes the "author" role into a durable scheduler plus a
policy engine. 1.0 had vocabulary for everything the *production* loop touches — patches,
candidates, findings, revisions — and nothing at all for the loop that runs it. This
module is that gap: what a human tells the system, what the system decided and why, what
it could not decide, and what it reports at the end of a day.

Two design notes that are easy to get backwards.

**A policy decision is evidence, not a verdict flag.** ``PolicyDecisionRecord`` carries
every gate result that ran, in order, including the ones that passed, plus the provider
and profile that produced the candidate. PLAN.md section 2 requires every generated claim
to be traceable to exact inputs and tool versions; a record that stored only
accept/reject would satisfy the letter and lose the reason. The shape here is taken from
what LitHarness's draft handler already writes into its event payloads, so it is
consumer-proven rather than designed ahead of a consumer.

**No gate verdict may originate from the model that produced the candidate.**
``GateResult.verdict_source`` exists to make that checkable rather than assumed — it is
MirrorBench's central methodological invariant (model self-report is not a correctness
signal), and PLAN.md section 20.8 asks for exactly this discriminator. A record whose
source is ``model_self_report`` is not evidence of quality and must never be treated as a
passing gate.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from .envelope import ArtifactMeta
from .ids import ResourceRef


class DirectiveKind(str, enum.Enum):
    """What altitude a director is steering at (PLAN.md section 4.3)."""

    PREMISE = "premise"
    CONSTRAINT = "constraint"
    ARC_NOTE = "arc_note"
    TONE_NOTE = "tone_note"
    CHAPTER_NOTE = "chapter_note"
    #: A refusal. Vetoes are durable and outrank generated plans.
    VETO = "veto"
    #: Operational rather than creative: pause, resume, budget, publication policy.
    CONTROL = "control"
    UNKNOWN = "unknown"


class DirectiveStatus(str, enum.Enum):
    #: Captured durably; not yet read by a planner.
    RECEIVED = "received"
    #: Converted into versioned plan constraints, with the interpretation recorded.
    INTERPRETED = "interpreted"
    #: Interpreted and now binding on generation.
    APPLIED = "applied"
    #: Could not be reconciled with existing locked constraints; escalated.
    CONFLICTED = "conflicted"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


@dataclass
class Directive:
    """One durable instruction from the director.

    ``interpretation`` is deliberately separate from ``body``: the human's words are kept
    verbatim and immutable, and what the system decided they *meant* is recorded beside
    them for audit. Collapsing the two would make a misinterpretation invisible after the
    fact, which is the failure this separation exists to prevent.
    """

    meta: ArtifactMeta
    directive_id: str
    kind: DirectiveKind
    body: str
    status: DirectiveStatus = DirectiveStatus.RECEIVED
    book_id: str | None = None
    branch_id: str | None = None
    #: What the directive is about, when it is scoped to part of the book.
    targets: list[ResourceRef] = field(default_factory=list)
    #: The system's reading of `body`, recorded rather than inferred later.
    interpretation: str | None = None
    #: Plan constraints this directive produced, once interpreted.
    produced_constraint_ids: list[str] = field(default_factory=list)
    received_at: str | None = None
    interpreted_at: str | None = None
    #: Higher wins when two directives conflict. Vetoes should outrank suggestions.
    precedence: int = 0
    superseded_by: str | None = None


class GateKind(str, enum.Enum):
    """The acceptance ladder of PLAN.md section 4.2, in the order it runs."""

    #: Parseable, in scope, within length and structure limits, locks untouched.
    SHAPE = "shape"
    #: Game-system replay, ledger arithmetic, continuity detectors, mechanical vetoes.
    INTEGRITY = "integrity"
    #: Calibrated critic thresholds. Advisory until calibration promotes them.
    CRAFT = "craft"
    #: Per-operation, per-day and per-book ceilings, in invocations as well as tokens.
    BUDGET = "budget"
    UNKNOWN = "unknown"


class VerdictSource(str, enum.Enum):
    """Where a gate verdict came from. See the module docstring.

    ``MODEL_SELF_REPORT`` exists to be *recorded and refused*, not to be trusted. It is
    named so that a system which accidentally routes one into a blocking gate can be
    caught by inspection rather than by reading the code that produced it.
    """

    #: Computed by code. The only source a blocking gate may rely on before calibration.
    DETERMINISTIC = "deterministic"
    #: A model judging an artifact it did not produce, under a frozen, order-randomized
    #: protocol with measured held-out precision.
    CALIBRATED_CRITIC = "calibrated_critic"
    #: A model judging an artifact it did not produce, without calibration evidence.
    #: Annotation only; never blocking.
    UNCALIBRATED_CRITIC = "uncalibrated_critic"
    #: A human judgment, from audit sampling or a calibration session.
    HUMAN = "human"
    #: The generating model's claim about its own output. Never a correctness signal.
    MODEL_SELF_REPORT = "model_self_report"
    UNKNOWN = "unknown"


@dataclass
class GateResult:
    """One gate's verdict, including the ones that passed.

    Passing results are kept because "which gates ran" is as much a part of the audit as
    "which gates failed" — a decision record that lists only failures cannot distinguish a
    candidate that passed the full ladder from one that was never checked.
    """

    gate: GateKind
    #: Stable identifier for the specific rule or critic, e.g. "shape.draft.v0".
    rule_or_critic_id: str
    passed: bool
    verdict_source: VerdictSource = VerdictSource.DETERMINISTIC
    #: Whether this gate can refuse. Uncalibrated critics annotate and never block.
    blocking: bool = True
    #: Named refusal reasons, for a retry that can act on them.
    vetoes: list[str] = field(default_factory=list)
    detail: str | None = None
    score: float | None = None
    threshold: float | None = None
    #: Calibration evidence backing a blocking craft gate. Absent means uncalibrated.
    calibration_id: str | None = None


class PolicyOutcome(str, enum.Enum):
    """The decisions of PLAN.md section 4.2. Retry ladders are bounded everywhere; the
    failure mode is a parked unit plus an exception, never a spin loop."""

    ACCEPT = "accept"
    RETRY = "retry"
    #: Spawn a detect-repair job for a located complaint.
    REPAIR = "repair"
    #: Fresh candidate, capped.
    REGENERATE = "regenerate"
    #: Mark the unit stuck and work elsewhere in the book.
    PARK = "park"
    ESCALATE = "escalate"
    UNKNOWN = "unknown"


@dataclass
class PolicyDecisionRecord:
    """Why one candidate was accepted, refused, or escalated.

    This is the artifact that makes "no proposal becomes canon merely because a model
    returned it" auditable after the fact rather than merely stated.
    """

    meta: ArtifactMeta
    decision_id: str
    outcome: PolicyOutcome
    #: What was being decided about.
    subject: ResourceRef | None = None
    job_id: str | None = None
    #: Every gate that ran, in order, passing ones included.
    gates: list[GateResult] = field(default_factory=list)
    #: Provenance of the candidate under judgment. A gate failure from a degraded
    #: fallback is a different diagnosis from one from the primary provider.
    provider: str | None = None
    model: str | None = None
    profile: str | None = None
    fell_back_from: list[str] = field(default_factory=list)
    #: Invocations as well as tokens: the CLI adapters' per-call harness tax scales with
    #: call count, so token accounting alone hides it (PLAN.md section 15).
    invocations: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None
    #: Digest of the frozen policy configuration this decision was made under, so a
    #: threshold change is visible as a different config rather than an unexplained
    #: change in behaviour.
    policy_config_digest: str | None = None
    attempt: int = 0
    decided_at: str | None = None
    resulting_revision_id: str | None = None
    escalation_id: str | None = None


class ExceptionKind(str, enum.Enum):
    REPEATED_GATE_FAILURE = "repeated_gate_failure"
    #: Two locked constraints cannot both be satisfied. Needs a director, not a retry.
    CONSTRAINT_CONFLICT = "constraint_conflict"
    BUDGET_EXHAUSTED = "budget_exhausted"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    #: Outward-facing posting always follows a configured policy.
    PUBLICATION_DECISION = "publication_decision"
    INTEGRITY_VIOLATION = "integrity_violation"
    UNKNOWN = "unknown"


class ExceptionStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    #: Closed without action, deliberately.
    DISMISSED = "dismissed"
    UNKNOWN = "unknown"


@dataclass
class ExceptionRecord:
    """An escalation policy could not resolve. Parks its own unit and nothing else."""

    meta: ArtifactMeta
    exception_id: str
    kind: ExceptionKind
    summary: str
    status: ExceptionStatus = ExceptionStatus.OPEN
    subject: ResourceRef | None = None
    job_id: str | None = None
    #: The decision that gave up, so the gate trail is one hop away.
    decision_id: str | None = None
    #: What a human could do about it. Options, not a free-text plea.
    suggested_actions: list[str] = field(default_factory=list)
    raised_at: str | None = None
    resolved_at: str | None = None
    resolution: str | None = None
    #: The directive that resolved it, when a human answered with one.
    resolved_by_directive_id: str | None = None
    attempts: int = 0


@dataclass
class DigestEntry:
    """One period's operating report (PLAN.md section 4.3).

    Deliberately carries the counts a director needs to notice trouble — parked units,
    open exceptions, spend against budget — and deliberately does *not* present word
    count as an achievement. PLAN.md section 1a.5 makes volume an explicit anti-goal,
    and a report that leads with words drafted will drift the system toward producing
    them.
    """

    meta: ArtifactMeta
    digest_id: str
    period_start: str
    period_end: str
    book_id: str | None = None
    ticks: int = 0
    jobs_succeeded: int = 0
    jobs_failed: int = 0
    #: Stuck, not lost. A growing number here is the signal the digest exists to surface.
    units_parked: int = 0
    candidates_accepted: int = 0
    candidates_refused: int = 0
    findings_opened: int = 0
    findings_closed: int = 0
    exceptions_open: int = 0
    words_accepted: int = 0
    invocations: int = 0
    total_tokens: int = 0
    spend_usd: float | None = None
    budget_usd: float | None = None
    #: Accepted work sampled for human spot-reading, per the standing audit policy.
    audit_samples: list[ResourceRef] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
