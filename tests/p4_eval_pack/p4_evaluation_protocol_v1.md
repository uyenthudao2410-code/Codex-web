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

### Canonical robustness gate v4

Before P5 controlled treatment may open, a representative P4 signal must now pass all four canonical conditions:

1. positive pooled leave-one-out Brier gain;
2. at least one Bonferroni-familywise Wilson-separated signal bucket pair;
3. positive leave-one-task-family-out Brier gain, with every observed task-family fold evaluable;
4. positive Brier gain on the later one-third temporal holdout trained only on the earlier two-thirds, with repair outcome variation on both sides of the split.

This makes pooled task-family proxies and late direction reversals fail closed instead of being promoted. It remains an association gate, not a causal claim. Source-state drift is still reported explicitly and no synthetic challenge may make a canonical signal promotion-eligible.

The deep challenge runner is:

```bash
python tests/p4_eval_pack/run_p4_deep_challenges.py --repo-root .
```

It uses only in-memory synthetic challenge rows, runs the canonical reporter before and after, and requires semantic readiness to be unchanged. Its synthetic rows are always `promotion_eligible=false`.

The exact controlled-P5 transition target remains fail-closed: `p4_gate.can_answer_which_signals_predict_repair=true`, at least one canonical `validated_signal`, `p4_empirically_complete=true`, a clean/upstream-matched P5 source baseline, and `p5_controlled_treatment_may_be_opened=true`. `p5_automatic_start` and global automatic policy activation remain false.

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

## Research-driven stress suite v1

P4 also has a literature-inspired adversarial suite that is intentionally broader than the 96-case engineering battery and the eight v4 deep challenges:

```bash
python tests/p4_eval_pack/run_p4_research_stress_suite.py --repo-root .
```

The suite translates published evaluation failure mechanisms into deterministic P4 counterexamples. The papers motivate the *failure mechanisms*; they do not prescribe this repository's gate. The mapping is therefore an engineering inference, and every row remains `source_class=synthetic_benchmark`, `promotion_eligible=false`, and forbidden from mutating canonical readiness.

Research themes encoded by the runner include:

- temporally consistent validation and future-information leakage (`temporally_consistent_validation_2025`);
- delayed verification / immature labels in just-in-time defect prediction (`jit_sdp_verification_latency`);
- precision-recall diagnostics under severe class imbalance (`saito_rehmsmeier_2015_pr_imbalance`);
- robustness and reliability under noisy labels (`olmin_lindsten_2022_noisy_labels`);
- local calibration failures hidden by global averages (`luo_et_al_2022_local_calibration`);
- spurious features and worst-group behavior under distribution shift (`zhou_et_al_2021_spurious_shift`);
- temporal distribution shift and rolling assessment (`han_huang_wang_2024_temporal_shift`);
- multiple-comparison discipline (`demsar_2006_multiple_datasets`).

The stress suite has six families of checks: data/label integrity, temporal drift, class imbalance/statistical power, subgroup/source-state robustness, metamorphic invariants, and out-of-sample empirical-bucket reliability diagnostics. Calibration checks use probabilities estimated from training bucket outcomes only; the ordinal `low/medium/high` risk labels are never treated as native probabilities.

Unlike the canonical promotion gate, this suite is expected to fail when it discovers a structural blind spot. A failing counterexample starts a replan: first reproduce and classify the failure, then harden the smallest canonical mechanism that actually permits the false promotion, then rerun this suite plus the existing v4 deep runner and focused P4 tests. Threshold relaxation, synthetic promotion, fabricated representative outcomes, and automatic P5 activation remain forbidden.

## Multilayer continuous challenge suite v1

The project also carries an independent model-facing benchmark that converts repository, web-agent, security, testing, contamination, terminal, and project-scheduling research into deterministic challenge/oracle pairs:

```bash
npm run benchmark:multilayer
```

The public challenge catalog is `tests/p4_eval_pack/challenges/multilayer_challenges_v1.json`. Hidden grading rules and reference responses are stored separately in `multilayer_oracles_v1.json`; candidate context should receive the public catalog, not the hidden oracle file. `research_sources_v1.json` records the primary publication or original benchmark identifier behind each challenge family.

The suite contains twelve layers: repository/cross-file reasoning; long-horizon engineering state; hidden-oracle traps; functional-plus-security correctness; web idempotency and optimistic concurrency; terminal/service causality; metamorphic relations; statistical robustness; contamination resistance; construction/project scheduling; adversarial agent-integrity traps; and continuous evaluation governance. Every public case is `source_class=synthetic_benchmark`, `promotion_eligible=false`, and forbidden from changing canonical readiness.

Scoring is multidimensional. A passed deterministic answer contributes to its named dimensions, an actual failure contributes zero, and missing/unobservable evidence remains `UNKNOWN` with a null score contribution rather than being coerced to zero. This preserves the repository-wide unknown-is-not-zero measurement rule.

The aggregate runner executes the existing research stress suite as a subordinate diagnostic and checks its exact reviewed signature from `known_diagnostics_v1.json`. The current baseline deliberately distinguishes three canonical blind spots from two fixture defects. In default regression mode those three blind spots are reported as `KNOWN_DIAGNOSTIC` and are not silently scored as passes or zeros; any signature drift, new failure, missing case, canonical before/after mutation, or promotion-policy violation fails the run and requires review.

For closure work, use the strict gate:

```bash
npm run benchmark:multilayer:strict
```

Strict mode remains nonzero while a known canonical blind spot is still reproduced. A future fix must therefore make the underlying counterexample pass and then deliberately update the reviewed diagnostic baseline; simply deleting a test, weakening an oracle, changing expected counts, or promoting synthetic evidence is not a valid closure.

To grade an external model or agent, save structured answers under a `responses` object and run:

```bash
python tests/p4_eval_pack/run_multilayer_challenge_suite.py --repo-root . --responses path/to/responses.json
```

Missing responses are `UNKNOWN` and make an external-response run `INCOMPLETE`; they are never treated as incorrect zero-valued observations. The default no-`--responses` mode grades hidden reference responses and therefore serves as a deterministic harness self-test plus continuous regression check.
