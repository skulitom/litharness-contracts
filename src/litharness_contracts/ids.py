"""Stable identifiers and evidence references.

``ResourceRef`` is the universal way to point at anything: a logical_id names
the narrative unit across versions; version_id (when present) pins one exact
immutable version. ``EvidenceSpan`` cites exact text: ``content_sha256`` is the
SHA-256 hex digest of the UTF-8 encoding of exactly ``text[start:end]`` of the
referenced source version, with offsets in Unicode code points. Exact hashes
are mandatory for span evidence (LitHarness PLAN section 11).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class ResourceKind(str, enum.Enum):
    MANUSCRIPT_BOOK = "manuscript_book"
    MANUSCRIPT_PART = "manuscript_part"
    MANUSCRIPT_CHAPTER = "manuscript_chapter"
    MANUSCRIPT_SCENE = "manuscript_scene"
    MANUSCRIPT_BLOCK = "manuscript_block"
    PLAN = "plan"
    ENTITY = "entity"
    ASSERTION = "assertion"
    STATE_EVENT = "state_event"
    RELATIONSHIP = "relationship"
    KNOWLEDGE = "knowledge"
    THREAD = "thread"
    WORLD_RULE = "world_rule"
    SUMMARY = "summary"
    EMBEDDING = "embedding"
    CONTEXT_PACKET = "context_packet"
    FINDING = "finding"
    GRAPH_NODE = "graph_node"
    GENERATION_CANDIDATE = "generation_candidate"
    REVISION_PLAN = "revision_plan"
    EXPORT_ARTIFACT = "export_artifact"
    JOB = "job"
    UNKNOWN = "unknown"


@dataclass
class ResourceRef:
    project_id: str
    book_id: str
    branch_id: str
    logical_id: str
    kind: ResourceKind
    version_id: str | None = None


@dataclass
class EvidenceSpan:
    source: ResourceRef
    start: int
    end: int
    content_sha256: str
    anchor_before: str | None = None
    anchor_after: str | None = None


@dataclass
class StoryPosition:
    """A position in narrative (story-internal) order.

    ``order_key`` sorts lexicographically within a branch. Wall-clock
    timestamps never determine narrative order (LitHarness PLAN section 11).
    """

    order_key: str
    label: str | None = None
