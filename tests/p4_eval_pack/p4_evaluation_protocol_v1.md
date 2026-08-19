# P4/MS1 Evaluation Battery v1

## Purpose

This battery evaluates the P4/MS1 measurement and readiness system. It is deliberately separated from canonical promotion evidence: every synthetic, generated, adversarial, or replay case is `promotion_eligible=false` and must run against isolated storage.

The canonical readiness decision remains the repository reporter:

```bash
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace .
```

Do not copy sample-count thresholds into this battery. The integration adapter must read the current canonical implementation so test code cannot silently diverge from the phase gate.

## Design

Total cases: **96** = 64 workflow challenges + 20 integrity cases + 12 statistical/readiness cases.

### Large-context strata

| Tier | Files | Relevant LOC | Dependency hops | Target symbols | Distractor ratio |
|---|---:|---:|---:|---:|---:|
| S | 1-3 | 100-800 | 0-1 | 1-4 | 20% |
| M | 4-10 | 800-4000 | 1-3 | 5-15 | 40% |
| L | 11-25 | 4000-15000 | 2-5 | 16-45 | 60% |
| XL | 26-60 | 15000-50000 | 4-8 | 46-120 | 75% |

### Workflow families

- **local_bugfix**: Fix a behavior defect with nearby misleading code and preserve boundary semantics. Oracle: Focused regression plus neighboring invariant tests.
- **api_feature**: Add an API capability while preserving backward compatibility and serialization contracts. Oracle: Contract tests, compatibility tests, and end-to-end request/response checks.
- **cross_file_refactor**: Refactor ownership or symbol boundaries across modules without behavior drift. Oracle: Full focused suite plus import/contract and semantic-equivalence checks.
- **test_ci_repair**: Repair a deterministic CI/test failure with environment and fixture interactions. Oracle: Reproducing failing test, targeted suite, and clean rerun.
- **data_schema_migration**: Evolve persisted schema with forward/backward compatibility and migration idempotence. Oracle: Round-trip migration, old/new fixtures, rollback or downgrade safety checks.
- **concurrency_lifecycle**: Fix ordering, lease, ownership, or stale-state behavior under interleaving events. Oracle: Deterministic concurrency schedule tests and state-machine invariants.
- **orchestration_state**: Preserve run/wave identity, acceptance ownership, and fail-closed orchestration transitions. Oracle: Ledger lineage assertions and state-transition tests across restart/reconcile boundaries.
- **performance_resource_boundary**: Separate resource pressure or queue noise from actual repair/rework causality. Oracle: Resource-admission fixtures plus functional proof that capacity noise does not relabel outcomes.

Each family is crossed with every context tier and two ground-truth outcomes (`first_pass_accepted`, `rework_required`), yielding 8 x 4 x 2 = 64 workflow cases. Metadata is intentionally rotated and includes counter-signal cases so a trivial rule such as 'low confidence means rework' cannot score perfectly.

## Five non-negotiable gates

1. **Measurement integrity gate**: 20/20 contract/integrity cases must behave fail-closed where specified. Missing shadow, wrong ownership, stale identity, duplicate ingestion, or missing proof/quality lineage cannot be silently accepted.
2. **Benchmark isolation gate**: running all 96 cases must leave the canonical P4 readiness population and result unchanged.
3. **Null-signal gate**: a large balanced null fixture must produce zero validated predictive signals. Duplicate rows and leakage must not create artificial support.
4. **Known-signal recovery gate**: an isolated fixture with a strong injected signal should be detectable by the evaluation path, while confounded or XL-reversing variants must be rejected or flagged unstable by the secondary robustness evaluator.
5. **Organic promotion gate**: only later, genuinely organic representative observations may affect canonical P4/MS1 readiness. The canonical reporter is the sole promotion authority.

## Statistical protocol

Use temporal ordering for development data: tune/inspect on earlier observations and evaluate on a later untouched holdout. Report class support explicitly. For skewed repaired/nonrepair outcomes, include precision/recall and PR-area diagnostics rather than relying on accuracy alone. If a probability/risk score exists, assess calibration separately from discrimination. These diagnostics do not replace the canonical reporter; they reveal whether a validated signal is likely robust enough to trust.

Recommended secondary diagnostics per candidate signal:

- repaired and nonrepair support counts by time window, context tier, and task family;
- precision, recall, F1, PR-AUC and false-positive/false-negative counts at the chosen decision rule;
- temporal holdout result and direction/effect stability across S/M/L/XL;
- family-stratified result to expose task-type confounding;
- bootstrap confidence interval or repeated time-block sensitivity analysis when sample size permits;
- calibration/reliability diagnostics only when the signal is interpreted probabilistically.

## Execution modes

### Mode A - unit/contract
Run C001-C020 using temporary state/ledger fixtures. No canonical workspace writes.

### Mode B - statistical fixtures
Run S001-S012 using isolated generated populations. Assert expected fail-closed, leakage, null-signal, and known-signal behavior. The generated rows are not representative observations.

### Mode C - large-context workflow challenge
Run W001-W064 in disposable worktrees or generated fixture repositories. Capture the same P4 evidence fields as normal work, but force benchmark provenance and `promotion_eligible=false`. Validate observed outcomes against ground truth and inspect signal behavior across context strata.

### Mode D - organic shadow evaluation
Observe normal feature/bugfix work without changing routing or manufacturing outcomes. Keep a time-ordered untouched holdout. Only this mode may feed canonical promotion evidence when repository provenance rules mark an observation eligible.

## Required P4 evidence fields

The adapter should preserve at least: workspace/measurement identity; run/wave identity; solution-shadow ordering; candidate scope; estimated files/lines/symbols; root-cause confidence; oracle strength; expected repair risk; smallest causal solution; actual patch surface; proof lineage/status; first-pass acceptance; replan/failure events; quality outcome; report ownership/lifecycle; and provenance/promotion eligibility.

## Stop conditions

Stop and fix the evaluation system before interpreting predictor quality if any integrity case silently passes invalid evidence, benchmark rows alter canonical readiness, duplicates inflate support, temporal leakage is not detectable, or run/wave/workspace identity can be crossed without rejection.

## Canonical close decision

A green battery means P4 measurement/readiness behavior is trustworthy under controlled challenge. It does **not** close P4/MS1. Closure remains fail-closed and requires the canonical reporter to become ready from organic representative evidence under the frozen measurement contract.
