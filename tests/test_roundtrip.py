"""Every artifact type round-trips through JSON without loss."""

from __future__ import annotations

import json

import pytest

import litharness_contracts as lc
from factories import sample_artifacts

ARTIFACTS = sample_artifacts()


@pytest.mark.parametrize("name", sorted(ARTIFACTS))
def test_roundtrip(name: str) -> None:
    original = ARTIFACTS[name]
    cls = lc.ARTIFACT_TYPES[name]
    payload = lc.to_jsonable(original)
    # Must survive an actual JSON encode/decode, not just dict conversion.
    payload = json.loads(json.dumps(payload))
    restored = lc.parse_artifact(cls, payload)
    assert restored == original


@pytest.mark.parametrize("name", sorted(ARTIFACTS))
def test_registry_covers_sample(name: str) -> None:
    assert isinstance(ARTIFACTS[name], lc.ARTIFACT_TYPES[name])


def test_none_fields_are_omitted() -> None:
    payload = lc.to_jsonable(ARTIFACTS["job_record"])
    assert "error" not in payload
    assert "input_digest" not in payload
