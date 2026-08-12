"""Small factories producing a populated instance of every artifact type."""

from __future__ import annotations

import litharness_contracts as lc

META = lc.ArtifactMeta(
    schema_version=lc.SCHEMA_VERSION,
    artifact_id="a-1",
    artifact_kind="test",
    created_at="2026-08-12T00:00:00Z",
    actor="test",
    tool=lc.ToolIdentity(name="pytest", version="0"),
)

REF = lc.ResourceRef(
    project_id="p", book_id="b", branch_id="br", logical_id="scene-1",
    kind=lc.ResourceKind.MANUSCRIPT_SCENE, version_id="v1",
)

SPAN = lc.EvidenceSpan(source=REF, start=0, end=4, content_sha256="ab" * 32)

MODEL = lc.ModelIdentifier(
    provider="local", model="test-model", version_or_digest="sha:x",
    request_profile="default", template_version="t1",
)


def sample_artifacts() -> dict[str, object]:
    patch = lc.BoundedPatch(
        meta=META, target=REF, base_version_id="v1", base_content_sha256="cd" * 32,
        ops=[lc.PatchOp(kind=lc.PatchOpKind.REPLACE_SPAN, target_span=SPAN, new_text="new")],
        idempotency_key="ik-1", licensed_by_finding_id="f-1",
    )
    finding = lc.Finding(
        finding_id="f-1", category=lc.FindingCategory.INVENTORY,
        status=lc.FindingStatus.OPEN,
        scope=lc.FindingScope(book_id="b", scene_ids=["scene-1"]),
        severity=lc.Severity.MAJOR, message="ghost item",
        primary_span=SPAN, supporting_evidence=[SPAN],
        confidence=0.9, confidence_basis=lc.ConfidenceBasis.DETERMINISTIC,
        claim={"item": "watch"},
        reproduction=lc.Reproduction(config_hash="c", policy_version="p1"),
    )
    change_set = lc.ChangeSet(
        meta=META, change_set_id="cs-1", base_revision="r1", target_branch="br",
        actor=lc.ChangeActor.AUTHOR,
        operations=[lc.ChangeOperation(
            kind=lc.ChangeOpKind.REPLACE_SPAN, logical_source_id="scene-1",
            before_hash="ab" * 32, after_hash="cd" * 32, detail={"quote": "x"},
        )],
        idempotency_key="ik-2",
        extracted_changes=[lc.ExtractedChange(
            kind=lc.ExtractedChangeKind.FACT_CHANGED, subject="s", predicate="p",
            before=1, after=2, evidence=[SPAN], confidence=0.8,
        )],
    )
    return {
        "manuscript_revision": lc.ManuscriptRevision(
            meta=META, book_id="b", branch_id="br", revision_id="r1",
            nodes=[lc.ManuscriptNode(
                logical_id="scene-1", kind=lc.NodeKind.SCENE, position_key="010",
                parent_logical_id="book", title="One", content="text",
                content_sha256="ef" * 32, version_id="v1", metadata={"k": 1},
            )],
        ),
        "bounded_patch": patch,
        "plan_snapshot": lc.PlanSnapshot(
            meta=META, book_id="b", branch_id="br", revision_id="r1",
            items=[lc.PlanItem(
                logical_id="plan-1", kind=lc.PlanKind.PROMISE, text="promise",
                authority=lc.PlanAuthority.INTENDED, locked=True, links=[REF],
            )],
        ),
        "state_snapshot": lc.StateSnapshot(
            meta=META, book_id="b", branch_id="br", revision_id="r1",
            records=[lc.StateRecord(
                record_id="rec-1", kind=lc.StateRecordKind.ASSERTION,
                subject="s", predicate="p", value={"n": 1},
                story_position=lc.StoryPosition(order_key="s1", label="scene 1"),
                authority=lc.StateAuthority.ACCEPTED_CANON,
                pov_visibility=["mara"], evidence=[SPAN], confidence=1.0,
            )],
            as_of=lc.StoryPosition(order_key="s6"),
        ),
        "state_candidate_batch": lc.StateCandidateBatch(
            meta=META, book_id="b", branch_id="br", base_revision_id="r1",
            candidates=[lc.StateCandidate(
                candidate_id="c-1",
                record=lc.StateRecord(
                    record_id="rec-2", kind=lc.StateRecordKind.EVENT,
                    subject="s", predicate="did", value="x",
                ),
                extraction_source=REF, rationale="extracted",
                status=lc.CandidateStatus.PROPOSED,
            )],
            idempotency_key="ik-3", expected_base_version="r1",
        ),
        "context_query": lc.ContextQuery(
            meta=META, query_id="q-1", operation=lc.ContextOperation.DRAFT_SCENE,
            target=REF, token_budget=1000, pov_character_id="mara",
            intent="draft", referenced_entities=["mara"],
            hard_requirements=[REF], model_context_limit=32000, policy_version="v1",
        ),
        "context_packet": lc.ContextPacket(
            meta=META, packet_id="pk-1", query_id="q-1", source_snapshot=REF,
            sections=[lc.PacketSection(name="local", items=[lc.ContextItem(
                item_id="i-1", kind=lc.ContextItemKind.EXACT_PROSE, source=REF,
                text="prose", token_count=2, authority=lc.StateAuthority.ACCEPTED_CANON,
                provenance=[SPAN], scores={"relevance": 0.9},
            )])],
            budget=lc.TokenBudget(limit=1000, used=900, reserved_output=100),
            consumed_sources=[REF],
            rejected_candidates=[lc.RejectedCandidate(reason="budget", item_id="i-2")],
        ),
        "generation_request": lc.GenerationRequest(
            meta=META, request_id="gr-1", kind=lc.GenerationKind.REPAIR,
            target=REF, model=MODEL, idempotency_key="ik-4",
            context_packet_id="pk-1",
            params=lc.GenerationParams(temperature=0.7, max_tokens=800, seed=42),
        ),
        "generation_candidate": lc.GenerationCandidate(
            meta=META, candidate_id="gc-1", request_id="gr-1",
            status=lc.GenerationStatus.COMPLETE, patch=patch,
            token_usage=lc.TokenUsage(input_tokens=100, output_tokens=50),
            validations=[lc.ValidationOutcome(check="bounds", passed=True)],
        ),
        "evaluation_plan": lc.EvaluationPlan(
            meta=META, plan_id="ep-1", manuscript_revision=REF,
            detectors=[lc.DetectorSpec(detector_id="d-1", version="1")],
            state_snapshot=REF, critics=[lc.CriticSpec(critic_id="c-1", model=MODEL)],
            categories=[lc.FindingCategory.TIMELINE], seed=7,
        ),
        "evaluation_artifact": lc.EvaluationArtifact(
            meta=META, run_id="run-1", plan_id="ep-1", findings=[finding],
            errors=[lc.EvaluationError(stage="critic", reason="unparseable")],
            metrics={"precision": 1.0},
        ),
        "change_set": change_set,
        "impact_report": lc.ImpactReport(
            meta=META, report_id="ir-1", change_set_id="cs-1",
            impacts=[lc.ImpactItem(
                target=REF, impact_class=lc.ImpactClass.REVIEW_WARNING,
                confidence=0.7, reason="motive dependency",
                reason_paths=[[lc.ImpactPathEdge(
                    edge_type="motivated_by", from_ref=REF, to_ref=REF, authority="declared",
                )]],
            )],
            graph_version="g1", coverage_warnings=["no inferred edges"],
        ),
        "revision_plan": lc.RevisionPlan(
            meta=META, plan_id="rp-1", base_revision="r1", change_set_id="cs-1",
            steps=[lc.RevisionStep(
                step_id="s-1", target=REF, action=lc.StepAction.PROPOSE_REPAIR,
                approval=lc.ApprovalMode.AUTHOR_REQUIRED, finding_id="f-1",
                confidence=0.9, preservation_constraints=["untouched spans byte-identical"],
            )],
            graph_version="g1", estimated_cost={"tokens": 1200.0}, risks=["stale approval"],
        ),
        "run_manifest": lc.RunManifest(
            meta=META, run_id="run-1", purpose="test",
            inputs=[lc.InputRef(ref=REF, content_sha256="ab" * 32)],
            model=MODEL, code_version="0.1.0", outcome="succeeded",
        ),
        "job_record": lc.JobRecord(
            meta=META, job_id="j-1", job_kind="recompute_summary",
            status=lc.JobStatus.SUCCEEDED, attempts=1, idempotency_key="ik-5",
        ),
        "export_manifest": lc.ExportManifest(
            meta=META, export_id="x-1", manuscript_revision=REF,
            format=lc.ExportFormat.MARKDOWN,
            renderer=lc.ToolIdentity(name="renderer", version="1"),
            files=[lc.ExportFile(path="book.md", sha256="ab" * 32, size_bytes=1000)],
        ),
        "event_envelope": lc.EventEnvelope(
            schema_version=lc.SCHEMA_VERSION, event_id="e-1",
            event_type=lc.EventType.MANUSCRIPT_REVISION_ACCEPTED,
            created_at="2026-08-12T00:00:00Z", actor="test", project_id="p",
            idempotency_key="ik-6", book_id="b", branch_id="br", revision_id="r1",
            payload={"revision_id": "r1"}, payload_digest="ab" * 32,
        ),
        "gold_context_suite": lc.GoldContextSuite(
            meta=META, fixture_id="fx",
            cases=[lc.GoldContextCase(
                query=lc.ContextQuery(
                    meta=META, query_id="q-2", operation=lc.ContextOperation.EVALUATE,
                    target=REF, token_budget=500,
                ),
                mandatory=[lc.GoldContextTarget(reason="needed", span=SPAN)],
                forbidden=[lc.GoldContextTarget(reason="pov leak", ref=REF)],
            )],
        ),
        "gold_impact_suite": lc.GoldImpactSuite(
            meta=META, fixture_id="fx",
            cases=[lc.GoldImpactCase(
                scenario_id="e-1", description="rename", change_set=change_set,
                expected=[lc.GoldImpactExpectation(
                    target=REF, label=lc.ImpactLabel.MUST_UPDATE,
                )],
            )],
        ),
    }
