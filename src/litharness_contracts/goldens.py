"""Gold-label suite contracts for the shared fixtures.

These are the shapes the incubators consume as benchmark ground truth:
LongRangeContext scores packets against ``GoldContextSuite`` (mandatory /
forbidden targets per query); RevisionPropagation scores impact analysis
against ``GoldImpactSuite`` (expected labels per changed node).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .context import ContextQuery
from .envelope import ArtifactMeta
from .ids import EvidenceSpan, ResourceRef
from .propagation import ChangeSet


@dataclass
class GoldContextTarget:
    """A context item the packet must contain (mandatory) or must not
    contain (forbidden). Exactly one of ``span``/``ref`` should be set."""

    reason: str
    span: EvidenceSpan | None = None
    ref: ResourceRef | None = None


@dataclass
class GoldContextCase:
    query: ContextQuery
    mandatory: list[GoldContextTarget] = field(default_factory=list)
    forbidden: list[GoldContextTarget] = field(default_factory=list)
    notes: str | None = None


@dataclass
class GoldContextSuite:
    meta: ArtifactMeta
    fixture_id: str
    cases: list[GoldContextCase]


class ImpactLabel(str, enum.Enum):
    MUST_UPDATE = "must_update"
    INSPECT = "inspect"
    DERIVED_ONLY = "derived_only"
    SAFE_PRESERVE = "safe_preserve"
    UNKNOWN = "unknown"


@dataclass
class GoldImpactExpectation:
    target: ResourceRef
    label: ImpactLabel
    note: str | None = None


@dataclass
class GoldImpactCase:
    scenario_id: str
    description: str
    change_set: ChangeSet
    expected: list[GoldImpactExpectation]


@dataclass
class GoldImpactSuite:
    meta: ArtifactMeta
    fixture_id: str
    cases: list[GoldImpactCase]
