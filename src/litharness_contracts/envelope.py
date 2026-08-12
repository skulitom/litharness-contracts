"""The common artifact envelope carried by every top-level artifact.

Every envelope includes schema version, artifact ID, source revision(s),
created time, actor/tool, configuration digest, causal/correlation IDs,
warnings, and dependency refs (LitHarness PLAN section 11).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ids import ResourceRef


@dataclass
class ToolIdentity:
    name: str
    version: str


@dataclass
class ModelIdentifier:
    """Model identity for any model-involved artifact.

    Includes provider, model/version or digest where available, request
    profile, and template version (LitHarness PLAN section 11).
    """

    provider: str
    model: str
    version_or_digest: str | None = None
    request_profile: str | None = None
    template_version: str | None = None


@dataclass
class ArtifactMeta:
    schema_version: str
    artifact_id: str
    artifact_kind: str
    created_at: str
    actor: str
    tool: ToolIdentity
    source_revisions: list[ResourceRef] = field(default_factory=list)
    dependencies: list[ResourceRef] = field(default_factory=list)
    config_digest: str | None = None
    causation_id: str | None = None
    correlation_id: str | None = None
    warnings: list[str] = field(default_factory=list)
