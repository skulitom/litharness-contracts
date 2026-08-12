"""Manuscript revision and bounded patch contracts.

The manuscript IR is a typed ordered tree (LitHarness PLAN section 9.1).
A ``BoundedPatch`` is the only sanctioned shape for a prose change proposal:
it targets one node version, cites exact spans, and makes unchanged text
structurally ineligible for revision.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from .envelope import ArtifactMeta
from .ids import EvidenceSpan, ResourceRef


class NodeKind(str, enum.Enum):
    BOOK = "book"
    PART = "part"
    CHAPTER = "chapter"
    SCENE = "scene"
    BLOCK = "block"
    UNKNOWN = "unknown"


class BlockKind(str, enum.Enum):
    """What a ``BLOCK`` node contains. 1.1 addition.

    LitHarness PLAN.md section 11 requires game-system displays — status windows,
    level-up notices, quest text — to be *data* rather than decoration, so that diffing,
    evidence spans, detection and export treat system voice like any other span. 1.0 had
    a bare ``NodeKind.BLOCK`` with nowhere to put the machine payload, and neither golden
    fixture contained a single block node, so nothing had ever exercised it.

    ``PROSE`` is the escape hatch for a block that is not a system display.
    """

    PROSE = "prose"
    STATUS_WINDOW = "status_window"
    LEVEL_UP = "level_up"
    QUEST_LOG = "quest_log"
    SYSTEM_MESSAGE = "system_message"
    UNKNOWN = "unknown"


class LockKind(str, enum.Enum):
    """Why a node is frozen. 1.1 addition, and strictly richer than ``locked: bool``.

    A boolean cannot distinguish "the director vetoed this sentence" from "this chapter
    is published and changing it needs an erratum policy" (PLAN.md section 16), and those
    two demand different handling on every path that would touch the node.

    ``locked`` remains and remains authoritative for consumers that only understand it:
    a producer sets ``locked = kind is not NONE``, so a 1.0 reader still sees every lock
    and never mistakes a frozen node for a free one. That is what keeps this additive.
    """

    NONE = "none"
    #: Text frozen; children and ordering may still change.
    CONTENT = "content"
    #: Children and ordering frozen; text may still change.
    STRUCTURE = "structure"
    #: Both frozen, and a change requires a publication-policy decision.
    PUBLISHED = "published"
    UNKNOWN = "unknown"


@dataclass
class ManuscriptNode:
    """One node version in the manuscript tree.

    ``lock_kind``, ``block_kind`` and ``block_payload`` are 1.1 additions. All three were
    carried in ``metadata`` by LitHarness's IR before they existed here — deliberately, so
    the wire shape would be proven by a consumer rather than guessed ahead of one. They
    are promoted now that it has been.
    """

    logical_id: str
    kind: NodeKind
    position_key: str
    parent_logical_id: str | None = None
    title: str | None = None
    content: str | None = None
    content_sha256: str | None = None
    version_id: str | None = None
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    # -- 1.1 additions --------------------------------------------------------------
    # Every one defaults to None rather than to a "natural" default like NONE, False or
    # {}. That is a compatibility requirement, not a style choice: the serializer omits
    # None and only None, so a field defaulting to LockKind.NONE would append
    # `"lock_kind": "none"` to every node ever written — changing the bytes of every
    # existing artifact and every content address derived from them. Absent means "not
    # stated by the producer", which is what a 1.0 producer actually means.
    #: Refines `locked`; never contradicts it. A producer setting this must also set
    #: `locked = kind is not NONE` so a 1.0 reader still sees the lock.
    lock_kind: LockKind | None = None
    block_kind: BlockKind | None = None
    block_payload: dict[str, Any] | None = None
    tombstoned: bool | None = None
    tombstone_reason: str | None = None


@dataclass
class ManuscriptRevision:
    meta: ArtifactMeta
    book_id: str
    branch_id: str
    revision_id: str
    nodes: list[ManuscriptNode]
    parent_revision_id: str | None = None


class PatchOpKind(str, enum.Enum):
    REPLACE_SPAN = "replace_span"
    INSERT_AFTER = "insert_after"
    DELETE_SPAN = "delete_span"
    UNKNOWN = "unknown"


@dataclass
class PatchOp:
    """One bounded edit. ``target_span`` cites the exact text being replaced or
    deleted (zero-length span for pure insertion); ``new_text`` is the
    replacement (absent for deletion)."""

    kind: PatchOpKind
    target_span: EvidenceSpan
    new_text: str | None = None


@dataclass
class BoundedPatch:
    meta: ArtifactMeta
    target: ResourceRef
    base_version_id: str
    base_content_sha256: str
    ops: list[PatchOp]
    idempotency_key: str
    licensed_by_finding_id: str | None = None
    author_request_id: str | None = None
