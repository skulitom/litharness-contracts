"""Run, job, and export contracts (LitHarness PLAN sections 13, 16, 21)."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

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
    meta: ArtifactMeta
    job_id: str
    job_kind: str
    status: JobStatus
    attempts: int = 0
    idempotency_key: str | None = None
    input_digest: str | None = None
    error: str | None = None


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
