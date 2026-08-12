# litharness-contracts

Neutral, versioned contracts and golden fixtures shared by the LitHarness
research program (see `C:\DEV\LitHarness\PLAN.md` §11, §27.2). The sibling
projects — BookWorldState, LongRangeContext, ContinuityEvaluation,
RevisionPropagation, and LitHarness itself — depend on this package's schemas
and fixtures **instead of importing each other**.

License: TBD — resolve alongside the BookWorldState license decision
(LitHarness PLAN §23.3) before anything is published.

## What is in here

| Path | Contents |
|---|---|
| `src/litharness_contracts/` | Python dataclasses for every contract type — the source of truth |
| `schemas/` | JSON Schema (draft 2020-12), generated from the dataclasses |
| `fixtures/source/` | Two golden six-scene books: prose (`.md`) + annotations (`def.json`) |
| `fixtures/golden/` | Generated, span-exact gold artifacts the incubators consume |
| `tools/` | `generate_schemas.py`, `build_fixtures.py` (regeneration commands) |
| `tests/` | Round-trip, compatibility, schema-drift, and fixture-integrity tests |

## Contract types

Envelope-bearing artifacts (parse with `parse_artifact`): `ManuscriptRevision`,
`BoundedPatch`, `PlanSnapshot`, `StateSnapshot`, `StateCandidateBatch`,
`ContextQuery`, `ContextPacket`, `GenerationRequest`, `GenerationCandidate`,
`EvaluationPlan`, `EvaluationArtifact`, `ChangeSet`, `ImpactReport`,
`RevisionPlan`, `RunManifest`, `JobRecord`, `ExportManifest`,
`EventEnvelope`, `GoldContextSuite`, `GoldImpactSuite`.

Value objects with standalone schemas: `ResourceRef`, `EvidenceSpan`,
`Finding`, `ContextItem`, `StateRecord`.

Shapes mirror the sibling PLANs: `Finding` follows ContinuityEvaluation §5,
`ContextQuery`/`ContextItem`/`ContextPacket` follow LongRangeContext §5/§12,
`ChangeSet`/`ImpactReport`/`RevisionPlan` follow RevisionPropagation §5/§10,
and the event vocabulary follows LitHarness §13.3.

## Compatibility rules (enforced by `_serde.py` and `tests/test_compat.py`)

- Additive fields are optional within a major version; unknown fields are
  ignored on read; `None` fields are omitted on write.
- Consumers reject unknown **major** schema versions
  (`IncompatibleSchemaVersion`); minor/patch drift is accepted.
- Every enum has an `unknown` member; unrecognized values decode to it
  instead of failing.
- `EvidenceSpan.content_sha256` is the SHA-256 of the exact UTF-8 span text
  `text[start:end]` (Unicode code-point offsets). Exact hashes are mandatory.
- Write-shaped artifacts (`BoundedPatch`, `ChangeSet`, `StateCandidateBatch`,
  requests) carry idempotency keys and expected base versions.
- Wall-clock timestamps never determine narrative order; use
  `StoryPosition.order_key`.

## The golden fixtures

Two six-scene books, annotated end to end. All IDs are deterministic (UUIDv5)
and timestamps fixed, so rebuilds are byte-stable.

**`mystery` — “The Vane House.”** Classic prose. Planted defects (8 open):
exclusive-location conflict, ghost item (the gold watch), life-status error
(Bruno), premature knowledge (Mrs. Brandt and the will), timeline
contradiction (the doctor's arrival), title drift (housekeeper→cook),
unresolved locked promise (the sealed letter), repeated beat (the vault-lock
explanation). Negative controls (3, `accepted_intentional`): the rain motif,
Julian's deliberate lie (belief vs truth), and Julian's floorboard knowledge —
apparent premature knowledge that scene 5 explains, i.e. the case a naive
knowledge detector must surface but the author overrules.

**`litrpg` — “The Toll Gate.”** Explicit game state via status blocks; the
status-snapshot records reproduce exactly what the prose says, so defects are
mechanically checkable arithmetic. Planted defects (6 open): gold-ledger
error (25 − 5 ≠ 15), skill used before acquisition (Shadowstep), HP over
locked ceiling (34/30), level regression (4→3) against a locked world rule,
quest marked completed before its completion event, ghost item (the silver
key). Negative controls (2): System flavor text with no stat change, and the
intentionally repeating status-block format.

> **Known inconsistency in the `litrpg` ghost-item defect.** `rec-ev-silver-key`
> (`used_item`, `silver_key`) is the planted ghost item, and `rec-ev-potion`
> (`consumed`, `red_potion`) is structurally identical to it — no acquisition record
> anywhere in the 19 records, and absent from every prose `[INVENTORY]` block — yet
> only the silver key is labelled a defect. Consuming an item you never had is equally
> a ghost, so the only mechanical discriminator available to a detector is the
> predicate name: `used_item` versus `consumed`.
>
> The consequence is measurable. A principled ghost rule emits **seven** findings
> against six gold, and narrowing the rule to `used_item` to reach 6/6 leaves it with a
> fixture population of exactly one — a check barely distinguishable from `assert
> True`. ContinuityEvaluation's `inventory.ghost.v0` currently takes the narrow scope
> and pins the asymmetry in `test_consumed_item_without_acquisition_is_not_reported`,
> which is the test that should fail and be rewritten when the fixture changes.
>
> Two fixture-side resolutions: label `red_potion` as a second ghost-item defect, or
> give it an acquisition record so it becomes a negative control for the rule. The
> second is more valuable — it would give this check its only in-fixture negative
> example. Either way it is authored ground truth and therefore human work, and it must
> not be resolved by loosening the detector.

Per fixture, `fixtures/golden/<name>/` contains:

- `manuscript.json` — `ManuscriptRevision` with inline scene content and hashes
- `plans.json` — `PlanSnapshot` including locked constraints and promises
- `state.json` — `StateSnapshot` with span-exact evidence (incl. locked world
  rules and a POV-restricted record that is the forbidden-context trap)
- `findings.json` — `EvaluationArtifact` of gold findings with resolvable spans
- `context_gold.json` — `GoldContextSuite`: queries with mandatory/forbidden
  targets (ContinuityEvaluation and LongRangeContext consume this)
- `impact_gold.json` — `GoldImpactSuite`: edit scenarios (`ChangeSet`) with
  expected impact labels `must_update | inspect | derived_only |
  safe_preserve`, including a typography-only negative control
  (RevisionPropagation consumes this)

## Regeneration

```bash
uv run python tools/generate_schemas.py
uv run python tools/build_fixtures.py
uv run pytest
```

Editing prose or `def.json` and forgetting to rebuild fails
`test_golden_matches_rebuild`; editing a dataclass and forgetting to
regenerate fails `test_committed_schema_matches_generated`. Every evidence
span in every golden is re-resolved and hash-checked on each test run.

## Consumption rules for the incubators

1. Depend on this package (path dependency or pinned version); never import a
   sibling project.
2. Read goldens with `parse_artifact(<Type>, json.loads(...))` — this enforces
   the major-version gate.
3. Benchmark against `GoldContextSuite` / `GoldImpactSuite` / the gold
   `EvaluationArtifact` rather than inventing per-repo annotation formats.
4. Negative controls are as load-bearing as defects: reporting
   `f-control-*` items as defects is a benchmark failure (false positive).
5. Propose contract changes here first; additive-optional within 1.x, and any
   breaking change bumps the major version.
