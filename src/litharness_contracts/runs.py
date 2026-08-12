"""Run, job, and export contracts (LitHarness PLAN sections 13, 16, 21)."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from .envelope import ArtifactMeta, ModelIdentifier, ToolIdentity
from .ids import ResourceRef


@dataclass
class InputRef:
    ref: ResourceRef
    content_sha256: str | None = None


@dataclass
class RunManifest:
    meta: ArtifactMeta
    run_id: str
    purpose: str
    inputs: list[InputRef] = field(default_factory=list)
    model: ModelIdentifier | None = None
    code_version: str | None = None
    platform: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    outcome: str | None = None


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    POISONED = "poisoned"
    UNKNOWN = "unknown"


@dataclass
class JobRecord:
    """A durable unit of work.

    Four fields below are 1.1 additions, and all four are shapes a consumer proved
    rather than shapes this package guessed. LitHarness built its Conductor against the
    1.0 record, found each of them missing, carried them locally, and reported back —
    which is the order LitHarness PLAN.md section 20.3 asks for.

    **Leases** (``lease_holder`` / ``lease_expires_at``) were absent entirely from 1.0.
    They are what makes single-instance execution safe when a cron tick can overlap a
    still-running one: a holder id plus a wall-clock expiry, re-checked at every
    state-advancing write rather than trusted from claim time.

    **``payload``** exists because ``input_digest`` is a hash. A digest proves two
    enqueues describe the same work and collapses a replay; it cannot reconstruct what
    the work *was*, so a 1.0 handler received a record it could not act on. That gap
    blocked LitHarness's provider wiring for a full slice while the cause was
    misattributed to missing subsystems.

    **``priority``** is the ordering key for policy-driven work selection. Optional and
    defaulting to 0, so a consumer that ignores it sees unchanged FIFO behaviour.
    """

    meta: ArtifactMeta
    job_id: str
    job_kind: str
    status: JobStatus
    attempts: int = 0
    idempotency_key: str | None = None
    input_digest: str | None = None
    error: str | None = None
    # 1.1 additions. All None-defaulted so an unset field is absent from the wire and a
    # 1.0 record round-trips byte-identically — see ManuscriptNode for the full argument.
    lease_holder: str | None = None
    lease_expires_at: float | None = None
    payload: dict[str, Any] | None = None
    priority: int | None = None


class ExportFormat(str, enum.Enum):
    MARKDOWN = "markdown"
    DOCX = "docx"
    TEXT = "text"
    EPUB = "epub"
    UNKNOWN = "unknown"


@dataclass
class ExportFile:
    path: str
    sha256: str
    size_bytes: int | None = None


@dataclass
class ExportManifest:
    meta: ArtifactMeta
    export_id: str
    manuscript_revision: ResourceRef
    format: ExportFormat
    renderer: ToolIdentity
    settings_digest: str | None = None
    files: list[ExportFile] = field(default_factory=list)
