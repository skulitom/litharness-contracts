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


# --- 1.1 additive-minor guarantees -------------------------------------------------


def test_unset_one_one_fields_are_absent_from_the_wire() -> None:
    """The rule every 1.1 addition was shaped by, and the reason none of them default
    to a "natural" value like `LockKind.NONE`, `False` or `{}`.

    The serializer omits None and only None. A field defaulting to anything else would
    append a key to every artifact ever written — changing the bytes of existing payloads
    and every content address derived from them. This test is what makes that a checked
    property rather than a convention someone can forget.
    """
    node = lc.ManuscriptNode(logical_id="scene-1", kind=lc.NodeKind.SCENE, position_key="010")
    rendered = lc.to_jsonable(node)
    for added in ("lock_kind", "block_kind", "block_payload", "tombstoned", "tombstone_reason"):
        assert added not in rendered, f"unset 1.1 field {added} leaked into the payload"

    job = lc.JobRecord(
        meta=_payload("job_record")["meta"],
        job_id="j-1",
        job_kind="draft",
        status=lc.JobStatus.QUEUED,
    )
    rendered_job = lc.to_jsonable(job)
    for added in ("lease_holder", "lease_expires_at", "payload", "priority"):
        assert added not in rendered_job, f"unset 1.1 field {added} leaked into the payload"


def test_a_one_zero_payload_round_trips_byte_identically_under_one_one() -> None:
    """A 1.0 artifact parsed and re-serialized by 1.1 must be unchanged.

    This is the concrete meaning of "additive minor" for a system whose revision ids and
    evidence spans are content addresses: if a library upgrade silently rewrote payloads,
    every stored digest would stop matching its own artifact.
    """
    payload = _payload("manuscript_revision")
    payload["meta"]["schema_version"] = "1.0.0"
    restored = lc.parse_artifact(lc.ManuscriptRevision, payload)
    assert lc.to_jsonable(restored) == payload


def test_one_one_fields_survive_a_round_trip_when_set() -> None:
    node = lc.ManuscriptNode(
        logical_id="block-1",
        kind=lc.NodeKind.BLOCK,
        position_key="010",
        locked=True,
        lock_kind=lc.LockKind.PUBLISHED,
        block_kind=lc.BlockKind.STATUS_WINDOW,
        block_payload={"hp": 24, "level": 3},
    )
    restored = lc.from_jsonable(lc.ManuscriptNode, lc.to_jsonable(node))
    assert restored == node
    # `locked` stays authoritative for a 1.0 reader: it must agree with `lock_kind`.
    assert restored.locked is True


def test_lock_kind_and_block_kind_tolerate_unknown_values() -> None:
    """Enum additions must not break an older reader — the rule that lets 1.2 add a
    block kind without a coordinated upgrade."""
    payload = lc.to_jsonable(
        lc.ManuscriptNode(logical_id="b", kind=lc.NodeKind.BLOCK, position_key="010")
    )
    payload["block_kind"] = "holographic_minimap_from_1_9"
    payload["lock_kind"] = "sealed_by_a_later_version"
    restored = lc.from_jsonable(lc.ManuscriptNode, payload)
    assert restored.block_kind is lc.BlockKind.UNKNOWN
    assert restored.lock_kind is lc.LockKind.UNKNOWN


def test_conductor_artifacts_round_trip() -> None:
    meta = _payload("job_record")["meta"]
    decision = lc.PolicyDecisionRecord(
        meta=meta,
        decision_id="d-1",
        outcome=lc.PolicyOutcome.ACCEPT,
        gates=[
            lc.GateResult(
                gate=lc.GateKind.SHAPE,
                rule_or_critic_id="shape.draft.v0",
                passed=True,
            )
        ],
        provider="fake",
    )
    restored = lc.parse_artifact(lc.PolicyDecisionRecord, lc.to_jsonable(decision))
    assert restored.gates[0].rule_or_critic_id == "shape.draft.v0"
    # The default must be the only source a blocking gate may rely on.
    assert restored.gates[0].verdict_source is lc.VerdictSource.DETERMINISTIC


def test_every_conductor_event_type_is_constructible() -> None:
    """A producer cannot emit an event type this enum lacks — construction raises. These
    eight were unrepresentable in 1.0, which is what blocked directive ingestion."""
    for value in (
        "TickCompleted",
        "DirectiveIngested",
        "PolicyDecisionRecorded",
        "ExceptionRaised",
        "ExceptionResolved",
        "DigestPublished",
        "ProviderFellBack",
        "BudgetExhausted",
    ):
        assert lc.EventType(value).value == value


def test_parked_is_distinct_from_poisoned() -> None:
    """1.2's addition, and the reason it is not cosmetic: an operator reading the queue
    must be able to tell "the policy stopped this" from "this ran out of attempts"."""
    assert lc.JobStatus("parked") is lc.JobStatus.PARKED
    assert lc.JobStatus.PARKED is not lc.JobStatus.POISONED


def test_a_one_one_reader_degrades_parked_rather_than_failing() -> None:
    """Enum additions are additive for readers. A consumer built against 1.1 decodes an
    unknown status to UNKNOWN instead of raising — which is what makes shipping this a
    minor rather than a break."""
    payload = _payload("job_record")
    payload["status"] = "some_status_from_1_9"
    assert lc.parse_artifact(lc.JobRecord, payload).status is lc.JobStatus.UNKNOWN
