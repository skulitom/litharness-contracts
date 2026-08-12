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


@dataclass
class ManuscriptNode:
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
