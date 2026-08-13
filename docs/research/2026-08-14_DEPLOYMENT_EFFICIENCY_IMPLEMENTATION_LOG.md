# Deployment Efficiency Implementation Log — 2026-08-14

## Scope

Basis: `docs/research/2026-08-14_INDEPENDENT_DEPLOYMENT_EFFICIENCY_SCIENTIFIC_AUDIT.md`

Workspace: `E:\Github\Tools-Codex-web`

Base HEAD observed: `d3c6f184b8f5b2b3f603615f0e5a3abb889b9d0c`

Goal: implement measurable efficiency, lifecycle, reproducibility, and regression-test improvements while preserving existing project behavior.

## Implementation summary

### Performance trace v2

Changed: `resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py`

New aggregate research fields:

- `idempotency_key_calls`
- `proof_cache_hits`
- `execution_mode_counts`
- `route_resolved_counts`
- `orchestration_state_counts`

New per-event fields:

- `idempotency_key_present`
- `proof_cache_hits`
- `execution_mode`
- `route_requested`
- `route_resolved`
- `orchestration_state`

Existing trace files are read with version-2 defaults so older data remains readable.

### Runtime trace enrichment

Changed: `resources/coding-tools-mcp/coding_tools_mcp/server.py`

Tool traces now attach proof-cache count, explicit operation-key presence, and orchestration route/mode/state when present in the tool result.

### Stale-run lifecycle

Changed: `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`

Added `reconcile_stale_runs()`.

Default inactivity threshold: 24 hours.

Config: `CODING_TOOLS_MCP_STALE_RUN_SECONDS`.

Runtime range: 1 hour to 30 days.

A run is retained as active when it still has active execution ownership such as a running background operation, active/waiting lane, or active write lease. Reconciled runs keep their historical evidence and receive a `run_stale_reconciled` event.

### Reproducible routing economics benchmark

Added: `resources/coding-tools-mcp/benchmarks/routing_economics.py`

Added test: `resources/coding-tools-mcp/tests/test_routing_economics.py`

The harness invokes the production route selector directly.

Scenario v1 task mix:

| Class | Count | Route selected |
|---|---:|---|
| deterministic | 30 | deterministic |
| localized strong oracle | 35 | mini |
| bounded leaf | 20 | luna |
| broad/deep | 15 | sol_xhigh |

The output is explicitly labeled `scenario_simulation_not_production_ab` and serializes its assumptions.

Latest observed scenario result:

| Strategy | Credits | Accepted | Credits/accepted | TTA hours | Wasted attempts |
|---|---:|---:|---:|---:|---:|
| adaptive | 45.2597 | 98.3875 | 0.4600 | 0.3404 | 11.75 |
| all-Sol for model tasks | 92.1900 | 96.7500 | 0.9529 | 0.2453 | 0 |

Scenario credit difference: 50.91%.

This is a scenario result, not a production billing measurement.

### Root-level commands

Changed: `package.json`

Added:

- `npm run test:mcp`
- `npm run test:all`
- `npm run benchmark:routing`

This removes the earlier ambiguity around the Python package working directory.

### Efficiency regression tests

Added: `resources/coding-tools-mcp/tests/test_efficiency_runtime.py`

Coverage:

1. performance trace v2 fields and counters;
2. stale-run reconciliation preserves live work;
3. `.coding-tools` local state does not change source/worktree fingerprint while a tracked source change does.

## Audit correction: BASE_DRIFT

The current source already excludes `.coding-tools/` paths from the orchestration worktree fingerprint.

The new regression test confirms:

- adding `.coding-tools/volatile.json` does not change the fingerprint;
- changing tracked `app.py` does change the fingerprint.

Therefore the earlier audit hypothesis that local orchestration files may themselves explain the observed drift is not treated as confirmed root cause.

## Verification chronology

### Initial implementation proof

The implementation patch was applied, but the first test command ran from the repository root while referring to package-relative `tests/...` paths.

Observed result:

- exit code: 4
- classification: test harness working-directory error
- orchestration moved to REPLAN

Implementation wave report:

`.coding-tools/orchestration/reports/run-d9fb4b30edfb4aa190145e21fd072b72/`

### Focused verification with corrected package working directory

Result: **20 passed in 3.20 s**.

### Python suite excluding a concurrently edited capability file

Result: **135 passed + 3 subtests in 35.98 s**.

Previous audit baseline: 131 Python tests.

### Node/Electron suite

Result: **57/57 pass**.

TAP duration: **1964.7482 ms**.

`source root clean` passed.

Previous audit baseline: 51/51.

### Concurrent deep capability suite

The untracked file `resources/coding-tools-mcp/tests/test_system_capability_suite.py` was being edited concurrently during one full-suite run, which produced transient failures from an earlier version of the file.

After the file stabilized, direct run result: **34/34 pass in 9.72 s**.

A guarded edit attempt during the concurrent change returned `PATCH_CONTEXT_NOT_FOUND`; no fuzzy write was performed.

### Write-lease timing observation

One full Python run produced a timing-sensitive failure in an existing write-lease test that uses an 80 ms initial lease interval.

The same test had passed in earlier runs. A later full-suite retry passed.

A follow-up edit attempt was not applied because the current orchestration run required an explicit replan transition not available through the active client schema.

### Final Python acceptance run

Result: **169/169 pass in 46.19 s**.

### Final combined acceptance

- Python: 169/169
- Node: 57/57
- Total: **226/226 pass**

## Serialized tool-result benchmark

Command family: `benchmarks.tool_result_bytes`

Latest report:

`resources/coding-tools-mcp/benchmarks/reports/tool-result-bytes-20260814-020921.json`

Result:

| Metric | Value |
|---|---:|
| runs | 3/3 |
| tool calls/run | 9 |
| median bytes/call | 549 |
| mean bytes/call | 641.6 |
| min | 274 |
| max | 1689 |
| bytes/run | 5774, 5774, 5774 |
| median time/run | 0.531 s |

Comparison with the immediately preceding audit benchmark:

- median bytes/call: 549 -> 549
- mean bytes/call: 641.6 -> 641.6
- bytes/run: 5774 -> 5774
- median time/run: 0.532 s -> 0.531 s

Conclusion: the new research telemetry did not increase this benchmark's model-visible result size.

## Routing benchmark evidence

Canonical command: `npm run benchmark:routing`

Latest report:

`resources/coding-tools-mcp/benchmarks/reports/routing-economics-20260813-190928.json`

The scenario result differs slightly from the older prose estimate because the new harness makes its baseline definition and assumptions explicit. Reproducibility is preferred over forcing the output to match the previous report.

## Existing mechanisms confirmed during implementation

The current codebase already contains implementations and tests for:

- durable operation replay identity support;
- proof reuse using fingerprints;
- bounded handoff capsules;
- bundled agent workflow execution;
- background operation continuation;
- route and high-cost gates;
- orchestration state and write ownership.

This wave therefore concentrated on activation measurement, lifecycle hygiene, reproducible benchmarking, and regression evidence instead of creating duplicate subsystems.

## Recommendation status after this wave

| Audit item | Status |
|---|---|
| Measure/reduce round-trip cost | measurement improved; existing bundled workflow retained |
| Exclude volatile local state from source fingerprint | confirmed in source + regression test added |
| Operation replay/idempotency | existing core confirmed; usage coverage now measurable |
| Handoff capsule | existing core confirmed; concurrent UI work has tests |
| Proof reuse | existing core confirmed; proof-cache hits now measurable |
| Route ledger/calibration | existing route events + new reproducible scenario harness |
| Root-level Python test command | completed |
| Routing economics executable benchmark | completed |
| Tunnel operational counters | remains a follow-up measurement item |
| Automatic handoff trigger policy | remains a follow-up experiment |

## Files changed by the efficiency wave

Modified:

- `package.json`
- `resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py`
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`

Added:

- `resources/coding-tools-mcp/benchmarks/routing_economics.py`
- `resources/coding-tools-mcp/tests/test_efficiency_runtime.py`
- `resources/coding-tools-mcp/tests/test_routing_economics.py`

Generated evidence:

- `resources/coding-tools-mcp/benchmarks/reports/routing-economics-20260813-190255.json`
- `resources/coding-tools-mcp/benchmarks/reports/routing-economics-20260813-190928.json`
- `resources/coding-tools-mcp/benchmarks/reports/tool-result-bytes-20260814-020921.json`

The working tree also contains independent concurrent changes in Electron, renderer, control-panel tests, a deep capability suite, and research documents. Those are not attributed to this efficiency wave.

## Runtime activation status

All acceptance tests and benchmarks above instantiate or execute the new source successfully.

The desktop/MCP process serving the current chat was not forcibly restarted. A controlled runtime restart/reconnect is therefore still required before assuming the currently connected client has loaded every new source/schema change.

## Research metrics to collect after activation

Latency:

- calls per accepted run;
- wait time per accepted run;
- local execution time per accepted run;
- p50/p90 time to accepted;
- calls grouped by execution mode, route, and state.

Operation replay:

- explicit operation-key coverage;
- replay/dedup hits;
- duplicate executions avoided.

Proof reuse:

- proof-cache hit rate;
- saved verification time;
- invalid reuse incidents.

Long horizon:

- stale-run reconciliation count;
- handoff capsule rate for long tasks;
- resume success rate.

Routing:

- route distribution by task class;
- first-pass acceptance;
- repair turns;
- cost per accepted result;
- critical defects.

## Delivery state

- Source implementation: applied in working tree.
- Python acceptance: **169/169 pass**.
- Node acceptance: **57/57 pass**.
- Total: **226/226 pass**.
- Payload benchmark: pass, no size increase.
- Routing benchmark: pass, reproducible JSON scenario.
- Intermediate failures and replans: retained in orchestration/task evidence.
- Working tree: remains dirty because prior and concurrent work was preserved.
- Commit: not performed.
- Push: not performed.
- Runtime/service restart: not performed.

## Final assessment

This wave improves the three weakest engineering areas identified by the audit: **observability, reproducibility, and lifecycle hygiene**. It also converts the routing cost model from prose-only evidence into an executable scenario and adds regression evidence for source fingerprint behavior. The next optimization cycle should use the new trace data to measure real operation-key coverage, proof reuse, long-task handoff behavior, and round-trip cost before changing routing thresholds or adding more model orchestration complexity.
