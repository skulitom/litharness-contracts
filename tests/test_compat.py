"""Compatibility rules from LitHarness PLAN section 11."""

from __future__ import annotations

import copy

import pytest

import litharness_contracts as lc
from factories import sample_artifacts

ARTIFACTS = sample_artifacts()


def _payload(name: str) -> dict:
    return copy.deepcopy(lc.to_jsonable(ARTIFACTS[name]))


def test_unknown_enum_value_decodes_to_unknown() -> None:
    payload = _payload("evaluation_artifact")
    payload["findings"][0]["category"] = "a-category-from-the-future"
    restored = lc.parse_artifact(lc.EvaluationArtifact, payload)
    assert restored.findings[0].category is lc.FindingCategory.UNKNOWN


def test_every_contract_enum_has_unknown_member() -> None:
    import enum as enum_mod
    import litharness_contracts as pkg

    enums = [
        obj for obj in vars(pkg).values()
        if isinstance(obj, type) and issubclass(obj, enum_mod.Enum)
    ]
    assert enums, "expected contract enums to be exported"
    for e in enums:
        assert "unknown" in e._value2member_map_, f"{e.__name__} lacks an 'unknown' member"


def test_unknown_fields_are_ignored() -> None:
    payload = _payload("context_query")
    payload["a_future_optional_field"] = {"nested": True}
    payload["meta"]["another_future_field"] = 3
    restored = lc.parse_artifact(lc.ContextQuery, payload)
    assert restored == ARTIFACTS["context_query"]


def test_unknown_major_version_is_rejected() -> None:
    payload = _payload("context_query")
    payload["meta"]["schema_version"] = "2.0.0"
    with pytest.raises(lc.IncompatibleSchemaVersion):
        lc.parse_artifact(lc.ContextQuery, payload)


def test_minor_version_bump_is_accepted() -> None:
    payload = _payload("context_query")
    payload["meta"]["schema_version"] = "1.7.3"
    restored = lc.parse_artifact(lc.ContextQuery, payload)
    assert restored.meta.schema_version == "1.7.3"


def test_event_envelope_version_checked_at_top_level() -> None:
    payload = _payload("event_envelope")
    payload["schema_version"] = "9.0.0"
    with pytest.raises(lc.IncompatibleSchemaVersion):
        lc.parse_artifact(lc.EventEnvelope, payload)


def test_missing_schema_version_is_an_error() -> None:
    payload = _payload("context_query")
    del payload["meta"]["schema_version"]
    del payload["meta"]  # no meta and no top-level version at all
    with pytest.raises(lc.ContractError):
        lc.parse_artifact(lc.ContextQuery, payload)


def test_missing_required_field_is_an_error() -> None:
    payload = _payload("context_query")
    del payload["token_budget"]
    with pytest.raises(lc.ContractError):
        lc.parse_artifact(lc.ContextQuery, payload)


def test_int_accepted_where_float_expected() -> None:
    payload = _payload("evaluation_artifact")
    payload["findings"][0]["confidence"] = 1  # int, not float
    restored = lc.parse_artifact(lc.EvaluationArtifact, payload)
    assert restored.findings[0].confidence == 1.0
