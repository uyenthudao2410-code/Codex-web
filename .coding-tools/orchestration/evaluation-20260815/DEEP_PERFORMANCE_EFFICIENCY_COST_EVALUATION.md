# Tools-Codex-web — Deep Performance, Efficiency and Cost Evaluation

**Evaluation date:** 2026-08-15  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Observed HEAD:** `dff81e251836666fc825c40bf86e4167afd29c39`  
**Branch:** `main`  
**Worktree:** dirty; results describe the observed HEAD plus accepted uncommitted worktree changes.  
**North Star:** preserve quality/security first, then minimize total expected cost and time-to-accepted-result. Worker utilization and number of model calls are diagnostic only.

## 1. Executive verdict

The strongest measured performance finding is not model selection. It is **rework/replan cost**.

Across the historical accepted-run snapshot captured before this evaluation:

- accepted runs: **140**;
- first-pass accepted: **88 (62.86%)**;
- repaired/replanned: **52 (37.14%)**;
- overall accepted TTA: **p50 68.974 s**, **p90 321.334 s**.

For the same broad task class, repaired runs are commonly **about 2.7x–7.2x slower at p50** than first-pass runs. The biggest direct ROI opportunity is therefore reducing avoidable replan/rework, not making individual local MCP primitives a few milliseconds faster.

The deterministic MCP path itself is comparatively cheap on a small controlled fixture: a 9-tool-call workflow completed in a median **~0.882 s/run** across 10/10 runs with stable serialized result size. This does not prove all real tasks are cheap, but it does rule out basic tool serialization/dispatch as the dominant cause of 30–300 second accepted-result latency.

Output shaping has demonstrated positive ROI: only about **9.38%** of raw response bytes are exposed on the model-visible path, a reduction of about **90.62%**. Proof caching currently has little measured ROI: approximately **1 hit vs 107 misses**, with only **999 ms** saved cumulatively.

Exact monetary ROI between ChatWeb+MCP and Mini/Luna is **not yet measurable** because ChatWeb controller monetary/token usage is not observed and there are still **0 representative paired runs**. The correct state remains HOLD; unknown cost is not treated as zero.

A material cost-attribution defect was discovered during this evaluation: independent/unrelated OpenCode `message.updated` telemetry could be attached to whichever EOCL wave was currently projected, even when that wave was deterministic and external review was disabled. The historical ledger contains 23 such uncorrelated usage events with **$0.066656532 raw provider-reported cost**. Twenty-two of them were attached to the deterministic evaluation wave and accounted for **$0.066315982** raw cost. These are provider-spend observations, **not causally attributable task cost**. Source/test fixes now separate raw measured cost from causally attributed cost and reject uncorrelated OpenCode telemetry on non-OpenCode waves. The running MCP process has not been restarted after this source fix, so the guard is source-complete/tested but not yet live-active.

## 2. Evidence classification

Claims in this report use five evidence classes:

- **MEASURED:** deterministic local/runtime facts directly observed from tests, ledger or PerformanceTrace.
- **PROVIDER-REPORTED:** usage/cost values emitted by an external provider integration.
- **DERIVED:** arithmetic computed from measured facts.
- **SCENARIO:** simulation/benchmark assumptions; never treated as production A/B evidence.
- **UNKNOWN:** data the current system cannot observe reliably, especially ChatWeb monetary/token cost before MCP entry.

This distinction is mandatory for monetary conclusions. A provider can report that money was spent without proving that the spend belongs to the current accepted task.

## 3. Broad correctness and regression proof

Exact-worktree broad regression after the measurement-integrity fixes:

- root Node/Electron suite: **99/99 PASS**;
- Python MCP suite: **281 passed, 1 skipped** in **115.13 s**;
- `git diff --check`: PASS during focused EOCL waves;
- focused OpenCode / Execution Hub / ledger suite: **34/34 PASS**;
- focused ledger projection suite: **23/23 PASS**.

The previously observed `TOOLCALL_HANG` timeout-classification failure did not reproduce after the fixture was made less scheduler-sensitive. Production timeout semantics were not weakened; only the test fixture timeout was increased from 100 ms to 500 ms while the intentional stub hang remains 2 s.

## 4. Accepted-result TTA and rework tax

Historical runtime-activation snapshot:

| Task class | First-pass n | First-pass p50 | Repaired n | Repaired p50 | Repaired / first-pass p50 |
|---|---:|---:|---:|---:|---:|
| bugfix | 18 | 30.415 s | 5 | 140.764 s | ~4.63x |
| build_release | 4 | 45.026 s | 2 | 272.988 s | ~6.06x |
| custom | 1 | 15.928 s | 1 | 57.870 s | ~3.63x |
| diagnose | 15 | 75.141 s | 5 | 203.063 s | ~2.70x |
| feature | 23 | 36.357 s | 27 | 193.518 s | ~5.32x |
| greenfield | 2 | 17.295 s | 0 | — | — |
| refactor | 15 | 28.768 s | 7 | 85.535 s | ~2.97x |
| test_failure | 5 | 31.968 s | 5 | 229.810 s | ~7.19x |

Historical Mini/Luna `test_failure` rows exist, but they are benchmark/calibration evidence, not representative production pairs:

- Luna first-pass n=3, p50 30.868 s;
- Mini first-pass n=2, p50 23.177 s.

They must not be compared directly to production task mixes as a speedup claim.

### Interpretation

The largest performance multiplier currently visible is avoiding a failed first wave. Improvements that reduce ambiguous patches, stale assumptions, packet defects, invalid test selectors, or unnecessary proof repetition can save multiples of the execution time. This has much stronger evidence than speculative model-tier routing gains.

## 5. Deterministic MCP primitive overhead

Controlled `tool_result_bytes` microbenchmark:

- runs: **10/10 complete**;
- tool calls per run: **9**;
- total serialized result bytes: **66,290**;
- serialized result bytes per run: **6,629**, stable across all ten runs;
- median individual tool result: **640 bytes**;
- mean individual tool result: **736.6 bytes**;
- min/max individual tool result: **347 / 1,881 bytes**;
- total benchmark wall time: **8.812 s**;
- median workflow wall time: **~0.882 s/run**.

This is a small deterministic fixture, so it is not a production TTA benchmark. It does, however, show that the basic local tool-loop/serialization layer is not intrinsically tens of seconds slow.

## 6. Output shaping and context efficiency

Observed PerformanceTrace around the evaluation window:

- raw response bytes: ~**95.77 MB**;
- model-visible bytes: ~**8.98 MB**;
- model-visible/raw ratio: **~9.38%**;
- derived reduction before model-visible consumption: **~90.62%**.

Per-run raw response distribution from ~200 run metrics:

- p50 ~150 KB;
- p90 ~905 KB;
- p95 ~1.24 MB;
- p99 ~2.02 MB;
- max ~3.56 MB.

Per-run model-visible distribution:

- p50 ~390 bytes;
- p90 ~48.8 KB;
- p95 ~96.8 KB;
- p99 ~170 KB;
- max ~274 KB.

This is one of the clearest proven efficiency wins in the current design and should be preserved.

## 7. Local execution vs inter-tool gap

Observed cumulative trace values around this evaluation:

- local execution: ~**6.70 million ms**;
- `estimated_wait_ms`: ~**57.46 million ms**;
- ratio: roughly **8.6x**.

`estimated_wait_ms` is explicitly **not model latency**. It can include controller reasoning, scheduling, transport, UI/user delay and other gaps. Therefore it must not be converted to a model-speed claim. It does show that local execution is not the only or dominant end-to-end time component, so optimizing a few percent of local tool time alone cannot materially change total TTA.

## 8. Proof cache, continuation and idempotency

### Proof cache

Observed approximately:

- hits: **1**;
- misses: **107**;
- hit rate: **~0.93%**;
- cumulative time saved: **999 ms**;
- dominant miss reasons: cold input and input-fingerprint change.

Verdict: **HOLD**. Do not weaken fingerprints to increase the hit rate. Current evidence does not justify further proof-cache machinery.

### Large-result continuation

Observed result-tail samples exist, but there have been no representative truncation/continuation reads in the current workload. The feature is instrumented and source-fenced, but there is no demonstrated performance ROI yet.

Verdict: **HOLD / observe organically**.

### Idempotency

Current-policy key coverage remained **100%** in observed snapshots. This is primarily a correctness/retry-cost control rather than a latency optimization, but it prevents duplicate side effects and therefore caps catastrophic retry cost.

## 9. Routing and worker economics

Current representative paired evaluator after this deep test:

- ledger runs scanned in current state: **272**;
- representative tagged runs: **0**;
- valid Mini pairs: **0**;
- valid Luna pairs: **0**;
- Mini: **HOLD**;
- Luna: **HOLD**;
- automatic activation: **false**;
- total monetary comparison: incomplete because controller cost is unobserved.

Historical candidate/calibration delegations:

| Route | Attempts | Candidate outcome | Visible estimated credits | Evidence meaning |
|---|---:|---|---:|---|
| Mini | 7 | 3 accepted_candidate, 4 blocked | >=0.965942 | calibration only |
| Luna | 5 | 3 accepted_candidate, 2 blocked | >=0.879200 | calibration only |
| Sol xhigh | 13 | 0 accepted_candidate, 13 blocked | >=1.961125 | negative topology signal |
| Terra | 2 | 0 accepted_candidate, 2 blocked | >=0.407650 | experimental negative signal |

`>=` is intentional: some failed delegations have no captured economics, so visible credits are lower bounds, not complete cost.

For Sol xhigh, observed blocked reasons include:

- `candidate_model_not_completed`: 6;
- `PROMPT_TOO_LARGE`: 4;
- `candidate_scope_missing`: 3.

The completed-cost samples often consumed around a 30 s candidate deadline before failing. This topology has no demonstrated positive ROI and should remain off the automatic path.

## 10. OpenCode cost-attribution incident discovered by the evaluation

### What happened

During a deterministic evaluation wave with external review disabled, the old live runtime attached 22 independent OpenCode `message.updated` telemetry records to the active wave.

Observed on that contaminated wave:

- events: **22**;
- provider/model: `opencode-go/deepseek-v4-pro`;
- raw provider-reported cost: **$0.066315982**;
- input tokens: **97,510**;
- cached input tokens: **24,576**;
- output tokens: **10,848**;
- reasoning output tokens: **6,986**;
- provider-duration evidence observed earlier for those 22 records: approximately **320.9 s** in aggregate.

Across the full historical usage-event ledger there are currently 23 `opencode:message.updated` usage events:

- raw provider-reported cost: **$0.066656532**;
- input tokens: **102,263**;
- cached input tokens: **24,576**;
- output tokens: **10,904**;
- reasoning output tokens: **6,986**.

The remaining ~$0.00034055 corresponds to the earlier OpenCode flash canary.

### Why this is not task cost

All 23 historical usage events have provenance `opencode:message.updated`, not dispatch correlation. Before the fix, the server could fall back to the current task-state run/wave when telemetry arrived without a provider dispatch/delegation identity. Therefore provider spend was observable, but causal ownership by the current task was not proven.

The contaminated diagnostic run is now rejected and must not contribute to baseline economics.

### Source fix implemented and tested

The source now:

1. rejects uncorrelated OpenCode telemetry on a deterministic/Mini/Luna/Sol wave with `PROVIDER_TELEMETRY_ATTRIBUTION_UNAVAILABLE`;
2. preserves compatibility for a wave explicitly routed to OpenCode;
3. records attribution state (`correlated_dispatch` vs task-projected OpenCode route);
4. separates `provider_cost` from `attributed_provider_cost`;
5. exposes `attribution_complete` in compact evidence/session projections;
6. refuses to mark total accepted-result monetary cost complete unless provider usage is both measured and causally attributed.

Historical contaminated wave under the new source projection now correctly reports:

- `provider_cost = 0.066315982` — raw measured/provider-reported;
- `attribution_complete = false`;
- `attributed_provider_cost = null`.

This is the correct scientific distinction.

### Live limitation

The runtime process was restarted earlier to activate the ROI measurement policy, but **has not been restarted after this new attribution fix**. No second restart was authorized during this evaluation. Therefore the attribution guard is source-complete and regression-proven, but the currently loaded process still has the pre-fix behavior until a future explicitly authorized reload/restart.

## 11. Scenario routing simulation

The routing economics scenario benchmark passes and, under the current source policy, all synthetic tasks resolve deterministic while ROI evidence is insufficient. Its hypothetical all-Sol comparison shows substantial theoretical credit avoidance.

This is **SCENARIO evidence only**. It must not be reported as measured production savings. Its valid use is regression-testing the policy rule: no worker cost is created automatically before representative paired evidence exists.

## 12. What can and cannot be concluded about cost today

### Can conclude

- Basic deterministic MCP execution is cheap relative to real accepted-run TTA on small controlled work.
- Rework/replan causes multi-fold TTA inflation and is the strongest observed optimization target.
- Output shaping has a large demonstrated context-volume benefit.
- Proof cache currently has negligible measured benefit.
- Sol xhigh/Terra candidate topology has negative historical calibration evidence and should not be automatic.
- Raw OpenCode provider spend is observable, but historical `message.updated` events are not causally attributable to accepted tasks.
- The system now has source logic to distinguish measurement completeness from attribution completeness.

### Cannot conclude yet

- exact `$ / accepted result` for ChatWeb+MCP;
- exact marginal dollar saving of Mini or Luna;
- production Mini/Luna TTA improvement;
- production OpenCode ROI;
- model latency from `estimated_wait_ms`;
- representative route promotion thresholds.

The missing evidence is primarily ChatWeb controller usage/cost plus representative paired task tags from a client surface that can submit the new `evaluation` schema.

## 13. Optimization priority based on current evidence

1. **Measurement integrity / causal cost attribution** — source fix completed; activate live only with an explicitly authorized future restart.
2. **Reduce first-wave failure and replan frequency** — highest measured TTA multiplier.
3. **Collect organic ChatWeb+MCP baseline tasks** using the already-open baseline window; do not create fake workload.
4. **Run controlled Mini/Luna pairs only after representative baselines exist** and the client can submit evaluation tags.
5. **Keep Sol xhigh, Terra and external review off the automatic critical path** until positive expected value is demonstrated.
6. **Do not invest further in proof cache or large-result continuation yet**; current telemetry does not justify it.
7. **Do not optimize worker utilization as a KPI.** A zero-delegation task is optimal when ChatWeb+MCP wins on quality, cost and TTA.

## 14. Practical KPI set going forward

Primary:

- quality/security floor;
- total monetary cost per accepted result, only when measurement + attribution are complete;
- TTA p50/p90;
- first-pass acceptance rate;
- replan/rework count and cost.

Secondary diagnostics:

- time to first route/write/green proof;
- proof duration and proof-cache benefit;
- model-visible bytes / raw response bytes;
- candidate completion/block reasons;
- provider cost attribution completeness;
- route-specific marginal cost/TTA under paired evaluation.

Not success metrics:

- number of agents called;
- worker utilization percentage;
- number of model calls;
- number of orchestration transitions.

## 15. Current evaluation verdict

The project is already showing a strong **ChatWeb + deterministic MCP** core. There is no evidence that the system needs more orchestration calls to become efficient. The next material efficiency gains are more likely to come from **avoiding rework, preserving compact model-visible context, and making monetary attribution trustworthy**, then selectively proving that Mini/Luna can beat the baseline on specific task classes.

Until representative paired evidence exists, `auto -> deterministic` and review-default-off are economically correct fail-closed defaults.
