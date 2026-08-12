"""Author plans and intent.

Plans distinguish "intended", "possible", and "canonical in prose"
(LitHarness PLAN section 4.1); any statement can be locked.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .envelope import ArtifactMeta
from .ids import ResourceRef


class PlanKind(str, enum.Enum):
    PREMISE = "premise"
    BOOK_PLAN = "book_plan"
    CHAPTER_PLAN = "chapter_plan"
    SCENE_PLAN = "scene_plan"
    CONSTRAINT = "constraint"
    PROMISE = "promise"
    WORLD_RULE = "world_rule"
    UNKNOWN = "unknown"


class PlanAuthority(str, enum.Enum):
    INTENDED = "intended"
    POSSIBLE = "possible"
    CANONICAL_IN_PROSE = "canonical_in_prose"
    UNKNOWN = "unknown"


@dataclass
class PlanItem:
    logical_id: str
    kind: PlanKind
    text: str
    authority: PlanAuthority
    locked: bool = False
    scope: ResourceRef | None = None
    links: list[ResourceRef] = field(default_factory=list)


@dataclass
class PlanSnapshot:
    meta: ArtifactMeta
    book_id: str
    branch_id: str
    revision_id: str
    items: list[PlanItem]
