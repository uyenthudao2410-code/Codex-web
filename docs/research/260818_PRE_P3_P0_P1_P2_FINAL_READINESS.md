# Pre-P3 Final Readiness — P0 / P1 / P2 — 2026-08-18

**Purpose:** one concise authoritative decision record for whether the project may enter P3 after the P0/P1/P2 remediation sequence.

**Decision at this checkpoint:** `P3 NOT STARTED`.

The current project is ready for a P3 **controlled pilot only after one explicit lifecycle activation gate**: restart Coding MCP so the accepted P0 ExceptionGroup-boundary fix is live, then verify the new runtime instance with read-only truth/orchestration calls. No automatic placement/model promotion is authorized by this record.

---

# 1. P0 — intermittent TaskGroup / ExceptionGroup boundary

## Status

```text
source remediation          CLOSED / ACCEPTED / CHECKPOINTED
live activation             PENDING EXPLICIT RUNTIME RESTART
P3 gate                     BLOCKED UNTIL LIVE VERIFY
public smart-v3 contract    UNCHANGED / 8 TOOLS
```

## Durable source proof

```text
source HEAD at run          775d92716f90ada3cfa909d8f0069c46d204ab51
run_id                      cbffed4e2bee4ff4af90a43708407d3d
wave_id                     adf0bbcb34844192adcaef633f655db8
accepted_at                 2026-08-17T19:18:21.812Z
state                       CHECKPOINTED
integrity                   40 / 40 OK
proof fingerprint           981220b6988f838a239f513bf62d957e06a706b25563ec500459ac114575e10b
```

Accepted source/test surface:

```text
resources/coding-tools-mcp/coding_tools_mcp/errors.py
resources/coding-tools-mcp/coding_tools_mcp/server.py
resources/coding-tools-mcp/tests/test_exception_group_boundary.py
```

The runtime boundary now:

- recursively extracts bounded exception-group leaves;
- preserves a single causal `ToolFailure` code/category/retryability/details;
- reports mixed/multiple child failures as typed `ASYNC_TASK_GROUP_FAILED` with bounded child evidence;
- records structured result/trace instead of leaking raw `ExceptionGroup` from `Runtime.call_tool()`;
- preserves the eight-tool public contract.

Proof actually run:

```text
python scripts/check_module_size.py                                      PASS
scoped git diff --check                                                  PASS
python -m unittest tests.test_exception_group_boundary tests.test_efficiency_runtime
                                                                         PASS
```

## Remaining P0 activation gate

Before P3, explicitly restart/activate the runtime and require:

```text
new process_instance_id
new server_instance_id
workspace_context(detail=full) PASS
agent_workflow prepare PASS
no raw ExceptionGroup leakage
stale/orphan residue = 0
smart-v3 tool count = 8
```

Source-level closure is real; live closure is intentionally not claimed before that lifecycle action.

---

# 2. P1 — measurement integrity plus synthetic plumbing smoke

## Status

```text
P1 measurement contracts              CLOSED
P1.1 canonical baseline               CLOSED
P1.2 causal host denominator          CLOSED
P1.3 controller coverage contract     CLOSED
P1.4 quality-outcome contract         CLOSED
P1.5 typed error taxonomy             CLOSED / CHECKPOINTED
P1.6 representative regret report     CLOSED / CHECKPOINTED
synthetic instrumentation smoke       PASS
representative efficacy               NOT PROVEN
controller economics                  HOLD
model/placement automatic promotion   false
```

## Synthetic smoke actually run

Two pairs / four deterministic read-only runs, all with `provenance=synthetic`, identical exact Git-HEAD oracle semantics within each pair, explicit environment/cache/order identity, and explicit controller start/source telemetry:

| Pair | Arm | Run | Wave | Result |
|---|---|---|---|---|
| `P1-SMOKE-20260818-001` | control | `af3fae9c6fc24bae9c7beb4a6f3ebf4a` | `54e3e9dd50a54149b8e79f45b4f61919` | CHECKPOINTED + quality |
| `P1-SMOKE-20260818-001` | treatment | `f3dcd9802298423db4acd8994feddae9` | `9d2e3ee52cd54a0e960532b709e8f728` | CHECKPOINTED + quality |
| `P1-SMOKE-20260818-002` | control | `878cd06eaee04f9cb7332a71d814dfa4` | `19cca92d99974d42906a3aacb52f6fbd` | CHECKPOINTED + quality |
| `P1-SMOKE-20260818-002` | treatment | `cdcee59d186c4a0ea0f3d0cb7c7adf7a` | `9b393d0774e248e59443dffb684afd4c` | CHECKPOINTED + quality |

All four quality rows explicitly observed:

```text
oracle_pass=true
critical_defect_count=0
noncritical_defect_count=0
manual_fix_required=false
regression_escape=false
rollback_required=false
source=synthetic_instrumentation_smoke
```

Fresh canonical reporter capture:

```text
captured_at                             2026-08-17T19:29:22.080878Z
run_count                               579
accepted                                350
aborted                                 173
completed                                 7
stale                                    49

pair_tagged_runs                          4
unique_pair_ids                           2
eligible_experimental_runs                4
controller observed                       4 / 4
controller started_at                     4 / 4
controller source                         4 / 4 client_reported
controller token usage                    0 / 4 observed
controller monetary cost                  0 / 4 observed
promotion_economics                       HOLD
hold_reason                               controller_cost_coverage_incomplete

quality events                            4
experimental runs with outcome            4 / 4
experimental quality coverage             1.0
promotion_quality                         eligible_for_analysis
representative regret tagged_runs_scanned 0
automatic promotion                       false
```

The zero token/cost observation counts are missingness/coverage, **not measured zero cost**. Synthetic rows are deliberately excluded from representative regret/promotion evidence.

Host correlation:

```text
host_spans_total                   55
host_spans_with_run_binding        19
historical binding rate            34.5455%
causally eligible runs              3
eligible runs with exact span       2
eligible-run coverage               66.6667%
```

`N=3` is instrumentation evidence only.

Fresh organic/model-free accepted-result cohort, excluding synthetic and explicit model routes:

```text
accepted scanned               346
model-route excluded            16
organic/model-free accepted    330
first-pass                     209 = 63.3333%
repaired                       121 = 36.6667%
replans                        220
first-pass TTAR p50             52.875 s
repaired TTAR p50              251.271 s
median repair penalty            4.75217x
```

P1 therefore now proves that the plumbing can carry controlled enrollment/controller-start/quality data without contaminating representative evidence. It still does not prove server-first/model efficacy or cost economics.

---

# 3. P2 — rework diagnosis and readiness

## Status

```text
P2.1 stratified diagnosis           CLOSED
P2.2 conservative causal mapping    CLOSED WITH EXPLICIT UNCLASSIFIED
P2.3 countermeasure evaluation      CLOSED / CAUSAL EFFECT HOLD
P2 main implementation              CHECKPOINTED
P2 readiness reporting              CHECKPOINTED
P3                                  NOT STARTED
```

Canonical implementation:

```text
run_id       d8231d2e1d384197912fe48d8eb97906
wave_id      38c2df6ff6ff42348006c2133b32b666
state        CHECKPOINTED
```

Final readiness reporting:

```text
run_id            16c46b4098d14cfba2207226a3ad650f
wave_id           50dc3fd12732494d9597e08b8ee5dd74
accepted_at       2026-08-17T19:28:14.054Z
state             CHECKPOINTED
proof fingerprint f886182e40ff200f5254821570e7468e9c162bfd294c7859e0e64fcd8944a25f
```

Readiness metrics:

```text
representative/model-free accepted runs   330
failure events on repaired runs           223
mapped causal events                      105
unclassified structured events            118
mapped causal coverage                    47.0852%
largest unclassified class                CHECK_FAILED = 71

oracle-eligible runs                      330
oracle observed                            57
oracle strong                               2
oracle not strong                          55
oracle unknown                            273
oracle observation coverage               17.2727%
```

The report explicitly preserves:

```text
unclassified_zero_means_absent = false
unknown oracle is not imputed
zero planned cause without evidence is not proof of absence
```

Current feature hotspot:

```text
n             102
first-pass     50 = 49.0196%
repaired       52 = 50.9804%
replans       100
oracle seen     3
oracle unknown 99
p50 first-pass 44.724 s
p50 repaired  253.123 s
```

Other material strata:

- bugfix: `23/67 = 34.3284%` repaired, repaired p50 `298.213 s`;
- diagnose: only `13/60 = 21.6667%` repaired but repaired p90 `1,934.424 s`;
- test_failure: `5/19` repaired, first-pass p50 `27.878 s` vs repaired p50 `246.091 s`.

Mapped repair evidence remains:

```text
acceptance_correction     38 events / 31 runs
patch_context_ambiguity   33 / 27
source_base_drift         27 / 17
runtime_tool_failure       5 / 5
proof_timeout              2 / 2
```

Unclassified structured evidence remains:

```text
CHECK_FAILED               71
BUILD_VERIFICATION_FAILED  27
INVALID_ARGUMENT           11
PERMISSION_REQUIRED         6
EXECUTION_OWNER_INVALID     2
PATCH_FAILED                1
```

Do not reclassify these historically without stronger evidence.

Countermeasures remain:

```text
patch_preflight        HOLD / not causally estimable
workdir_resolution     HOLD / not causally estimable
semantic_localization  HOLD / not causally estimable
exact_source           HOLD / not causally estimable
recovery_fencing       HOLD / not causally estimable
```

Patch preflight has direct evidence of `70` known no-write failures stopped before run creation. No comparable frozen pre-intervention epoch exists to estimate an accepted-result treatment effect.

---

# 4. Final pre-P3 gate

P3 may begin only after all items below are satisfied:

1. **Activate P0 source fix:** explicit Runtime restart, new process/server identity, live truth/orchestration smoke, eight-tool contract unchanged.
2. **Freeze the experiment before outcomes:** experiment manifest/activation epoch and analysis identity are fixed before the first treatment result is inspected.
3. **Use representative intention-to-treat enrollment:** do not reuse P2's accepted-only diagnostic denominator.
4. **Isolate one treatment dimension:** `LOCAL_FIRST_V1` versus `SERVER_FIRST_DETERMINISTIC_V1`; task/source/oracle/controller/proof/risk/environment stay equivalent.
5. **Require exact eligibility evidence:** portable environment, no GUI/device/secret affinity, exact source identity, explicit strong oracle, safe fallback.
6. **Preserve missingness:** controller cost/tokens remain unknown when unavailable. No CAR/cost-per-accepted-result promotion claim without sufficient cost coverage.
7. **Record explicit quality outcomes:** accepted lifecycle state is not enough.
8. **Keep auto promotion disabled:** class-specific promotion only after quality and powered evidence gates pass.
9. **Pilot first:** 10–20 representative pairs are for instrumentation, variance, break-even and power planning, not confirmatory production proof.

Current phase boundary:

```text
P0 source remediation          CLOSED / CHECKPOINTED
P0 live activation             REQUIRED BEFORE P3
P1 measurement integrity      CLOSED
P1 synthetic plumbing         PASS
P1 representative efficacy    NOT PROVEN
P1 economics                  HOLD
P2 diagnostic/readiness       CLOSED / CHECKPOINTED
P2 remediation efficacy       NOT PROVEN / HOLD
P3                            NOT STARTED
```

---

# 5. Authoritative tracking documents

This concise record must be read together with:

```text
docs/research/260817_CURRENT_LEDGER_BASELINE.md
docs/research/260818_P2_REWORK_DIAGNOSIS_CLOSURE_AND_P3_HANDOFF.md
docs/research/260817_PROJECT_REAL_STATE_SCIENTIFIC_EVIDENCE_AND_FULL_EXECUTION_PLAN.md
```

The first two have pre-P3 addenda with the same current P0/P1/P2 boundary. Older dated sections remain useful chronology and must not be interpreted as newer than this record.

---

**End of final pre-P3 readiness record.**