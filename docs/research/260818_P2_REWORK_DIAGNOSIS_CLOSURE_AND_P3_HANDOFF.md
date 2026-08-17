# P2 Rework Diagnosis Closure and P3 Handoff — 2026-08-18

**Purpose:** close Phase P2 against the accepted implementation and fresh ledger evidence, record scientific limitations explicitly, and define the exact entry gate for Phase P3 before any server-first treatment run begins.

**Status:** `P2 CLOSED / ACCEPTED / CHECKPOINTED`

**Important distinction:** P2 is closed as a **diagnostic / observational rework baseline**. It does **not** prove that any existing remediation is causally effective. Countermeasure promotion remains `HOLD` wherever comparable pre/post or paired evidence is absent.

This report is the current authoritative P2 -> P3 handoff. Earlier dated sections in:

- `docs/research/260817_PROJECT_REAL_STATE_SCIENTIFIC_EVIDENCE_AND_FULL_EXECUTION_PLAN.md`
- `docs/research/260817_CURRENT_LEDGER_BASELINE.md`

remain historical chronology where they still say `P2.1 NEXT / NOT STARTED`; for current P2 status, this closure supersedes those stale boundary statements without rewriting their historical snapshots.

---

# 1. Final P2 verdict

```text
P2.1 stratified rework diagnosis       CLOSED / ACCEPTED
P2.2 structured repair-cause mapping   CLOSED / ACCEPTED WITH EXPLICIT UNKNOWN
P2.3 countermeasure evaluation         CLOSED / HOLD FOR CAUSAL EFFECT CLAIMS
P2 implementation EOCL                 CHECKPOINTED
P2 fresh canonical reporter            PASS
P3                                      NOT STARTED
```

What P2 now provides:

1. workflow-stratified accepted-result rework rates;
2. first-pass vs repaired TTAR distributions;
3. observed scope-size evidence from `context_prepared.selected_paths`;
4. observed oracle evidence from `oracle_preflight.strong_oracle`;
5. conservative mapping from structured failure evidence to repair-cause families;
6. explicit `unclassified` output when evidence is insufficient;
7. intervention status that refuses to manufacture causal effect estimates;
8. a P3 entry contract designed to create the treatment population P2.3 currently lacks.

No public MCP tool, DB schema, routing authority, release contract, or automatic model/placement policy was added for P2.

---

# 2. Source / run / wave / proof identity

Canonical P2 implementation:

```text
base source HEAD  b9b7ee1223351c2f7b2b6da7914c0de10e85de9c
run_id            d8231d2e1d384197912fe48d8eb97906
wave_id           38c2df6ff6ff42348006c2133b32b666
final state       CHECKPOINTED
ledger integrity  81 / 81 OK at closure audit
```

Implementation surface:

```text
resources/coding-tools-mcp/coding_tools_mcp/rework_diagnosis.py
resources/coding-tools-mcp/scripts/report_p2_rework_diagnosis.py
resources/coding-tools-mcp/tests/test_rework_diagnosis.py
resources/coding-tools-mcp/coding_tools_mcp/evaluation_report.py
resources/coding-tools-mcp/tests/test_evaluation_report.py
```

Proof actually run:

```text
fc8ed2d5c15040f9aa3f1b368fb42ac4
  module-size check
  PASS

336f648df17c4765835139664a29a411
  Python compile check
  PASS

d514f388370d4514811c3e299d7cac03
  scoped git diff --check
  PASS

8e3b177b163948889c6dfaaccc61992a
  python -m unittest tests.test_rework_diagnosis tests.test_evaluation_report
  PASS
```

The P2 reporter also completed successfully against the canonical live ledger after checkpoint.

---

# 3. Fresh canonical population at P2 closure

Fresh current-ledger reporter capture used for the P2 closure:

```text
captured_at = 2026-08-17T18:52:59.168654Z

total runs = 572
accepted   = 344
aborted    = 172
stale      = 49
completed  = 7
```

Organic/model-free accepted-result cohort:

```text
accepted runs scanned           = 344
explicit model-route excluded    = 16
organic/model-free accepted     = 328
first-pass accepted             = 207  (63.1098%)
repaired accepted               = 121  (36.8902%)
replan count                    = 220

first-pass TTAR p50             = 52,146 ms
first-pass TTAR p90             = 431,210 ms
repaired TTAR p50               = 251,271 ms
repaired TTAR p90               = 1,067,959 ms
repaired/first-pass p50         = 4.818605x
repaired/first-pass p90         = 2.476656x
```

Interpretation:

> Rework remains a material accepted-result penalty. In this accepted-only observational cohort, the repaired median is about 4.82x the first-pass median.

This is **not** a treatment-effect estimate and must not be used as one.

---

# 4. P2.1 — workflow-stratified rework diagnosis

| Workflow | n | First-pass | Repaired | Replans | First-pass p50 | Repaired p50 |
|---|---:|---:|---:|---:|---:|---:|
| feature | 101 | 48.5149% | **51.4851%** | 100 | 44.724 s | 253.123 s |
| diagnose | 59 | **77.9661%** | 22.0339% | 28 | 103.140 s | 295.258 s |
| bugfix | 67 | 65.6716% | 34.3284% | 38 | 54.615 s | 298.213 s |
| test_failure | 19 | 73.6842% | 26.3158% | 12 | 27.878 s | 246.091 s |
| build_release | 23 | 65.2174% | 34.7826% | 9 | 120.622 s | 250.672 s |
| custom | 34 | 61.7647% | 38.2353% | 22 | 91.597 s | 228.037 s |
| refactor | 23 | 69.5652% | 30.4348% | 11 | 27.045 s | 85.535 s |
| unknown | 2 | 100.0000% | 0.0000% | 0 | 17.179 s | n/a |

## 4.1 Main leverage finding

`feature` is the largest observed rework stratum in this cohort:

```text
feature repaired accepted = 52 / 121 total repaired accepted
                         ~= 43.0%

feature replans = 100 / 220 total replans
                ~= 45.5%
```

Within the feature stratum:

```text
repaired p50 / first-pass p50 ~= 5.66x
```

Therefore feature work is the strongest **observational rework leverage candidate**. This does not mean every P3 server-first task should be a feature task; P3 eligibility still requires portable deterministic validation, exact source identity, and a strong oracle.

`test_failure` has a large median repair multiplier (~8.83x), but its sample is much smaller (`n=19`). It should be retained as a diagnostic stratum, not promoted to the primary economic headline solely from the ratio.

---

# 5. Scope-size evidence and its limitation

P2 measures scope only from explicit `context_prepared.selected_paths` evidence. Unknown scope is not imputed.

| Workflow | Scope observed | Scope unknown | p50 paths | p90 paths |
|---|---:|---:|---:|---:|
| feature | 71 | 30 | 4 | 20 |
| diagnose | 57 | 2 | 11 | 21 |
| bugfix | 40 | 27 | 3 | 12 |
| test_failure | 11 | 8 | 0 | 1 |
| build_release | 19 | 4 | 0 | 13 |
| custom | 26 | 8 | 1 | 17 |
| refactor | 3 | 20 | 0 | 12 |
| unknown | 2 | 0 | 0 | 0 |

No run in the current scope-percentile population was censored by the event path cap.

Scientific constraint:

> Scope differences may help explain workload mix, but unknown scope remains material in several strata, especially feature, bugfix and refactor. P2 does not backfill it from file diffs or other post-outcome evidence.

---

# 6. Oracle-strength evidence and its limitation

P2 reports `oracle_preflight.strong_oracle` only when that event is explicitly present.

| Workflow | Oracle observed | Strong | Not strong | Unknown |
|---|---:|---:|---:|---:|
| feature | 3 | 0 | 3 | 98 |
| diagnose | 22 | 0 | 22 | 37 |
| bugfix | 3 | 1 | 2 | 64 |
| test_failure | 4 | 0 | 4 | 15 |
| build_release | 12 | 1 | 11 | 11 |
| custom | 13 | 0 | 13 | 21 |
| refactor | 0 | 0 | 0 | 23 |
| unknown | 0 | 0 | 0 | 2 |

This is the most important P2 measurement limitation before P3:

> **Oracle-strength coverage is too sparse to explain current workflow repair-rate differences by oracle strength.** Unknown is intentionally not imputed.

Therefore P2 does not claim that feature rework is caused by weak oracles, and it does not map generic `CHECK_FAILED` to `oracle_weakness`.

For P3, strong-oracle eligibility must be populated prospectively on every enrolled pair where the experiment contract requires it.

---

# 7. P2.2 — structured repair-cause diagnosis

Mapped cause families from structured evidence:

| Repair cause | Events | Affected repaired runs |
|---|---:|---:|
| acceptance_correction | 38 | 31 |
| patch_context_ambiguity | 33 | 27 |
| source_base_drift | 27 | 17 |
| runtime_tool_failure | 5 | 5 |
| proof_timeout | 2 | 2 |
| environment_workdir | 0 | 0 |
| missing_requirement | 0 | 0 |
| oracle_weakness | 0 | 0 |
| provider_capacity | 0 | 0 |
| wrong_root_cause | 0 | 0 |

A zero here means **no current structured evidence mapped into that causal family**. It must not be read as proof that the underlying phenomenon never occurs.

## 7.1 Structured failure classes deliberately left unclassified

P2 refuses to infer a causal family when the structured failure class is insufficient by itself:

```text
CHECK_FAILED                71
BUILD_VERIFICATION_FAILED   27
INVALID_ARGUMENT            11
PERMISSION_REQUIRED          6
EXECUTION_OWNER_INVALID      2
PATCH_FAILED                 1
-------------------------------
total unclassified          118 structured failure events
```

This is a deliberate scientific property, not an unfinished parser bug.

The largest diagnostic gap is:

```text
CHECK_FAILED = 71
```

P2 does **not** relabel these as `oracle_weakness`, `wrong_root_cause`, or `missing_requirement` without causal evidence.

Prospective experiments should emit more specific typed reason evidence where possible so later analyses can reduce this unknown bucket without historical relabeling.

---

# 8. P2.3 — countermeasure evaluation

| Intervention | Monitored cause | Fresh observed evidence | Causal effect status |
|---|---|---|---|
| patch_preflight | patch_context_ambiguity | 27 affected repaired runs / 33 events; 70 known no-write failures stopped pre-run | `HOLD / not causally estimable` |
| workdir_resolution | environment_workdir | 0 affected / 0 mapped events | `HOLD / not causally estimable` |
| semantic_localization | runtime_tool_failure | 5 affected / 5 events | `HOLD / not causally estimable` |
| exact_source | source_base_drift | 17 affected / 27 events | `HOLD / not causally estimable` |
| recovery_fencing | runtime_tool_failure | 5 affected / 5 events | `HOLD / not causally estimable` |
| solution_minimization_later | n/a | not active in P2 | `NOT ACTIVE` |

For active historical interventions, the common blockers are:

```text
no_comparable_pre_intervention_cohort
no_frozen_activation_epoch_for_effect_estimation
```

Therefore:

```text
effect_estimate = null
```

for every active P2 intervention.

## 8.1 What can be said about patch preflight

Direct guardrail evidence exists:

```text
PATCH_CONTEXT_AMBIGUOUS = 45
PATCH_CONTEXT_NOT_FOUND = 25
preflight avoided       = 70 known no-write failures
```

This proves the guardrail observed and stopped those known no-write failures before orchestration run creation.

It does **not** prove a causal percentage reduction in accepted-result rework because a frozen comparable pre-intervention cohort is absent.

Correct wording:

> Patch preflight is an observed guardrail with direct avoided-failure evidence; its accepted-result treatment effect remains unestimated.

Incorrect wording:

> Patch preflight reduced rework by X%.

No such X is currently defensible.

---

# 9. Supplemental P2 closure findings before P3

The P2 audit found no material source mutation that must be added before P3. The required additions are measurement/governance constraints.

## 9.1 P2 accepted-only cohort is diagnostic, not intention-to-treat

P2's central workflow report is an accepted-result observational cohort. That is appropriate for locating repair burden among accepted outcomes, but it introduces survivor selection if reused as a treatment denominator.

P3 must not copy this denominator.

P3 primary analysis must retain every assigned experimental replicate:

```text
accepted
failed
blocked
capacity-failed
activation-failed
fallback
```

where relevant to the treatment contract.

## 9.2 Freeze activation epoch prospectively

P2.3 cannot estimate historical intervention effects mainly because activation boundaries were not frozen into a comparable study design.

Before the first P3 treatment pair, the experiment must freeze at least:

```text
experiment_id
policy / policy_version
activation_epoch or manifest identity
pair_id
replicate_id
task_class
provenance
environment_id
oracle_id
cache_stratum
order_index
source/runtime/tool-contract fingerprints
```

This is a direct lesson from P2.3 and is a required P3 entry gate.

## 9.3 Oracle evidence must be prospective and complete enough for the selected cohort

P2 oracle coverage is sparse. P3 eligibility explicitly requires a strong oracle, so the new paired cohort must record the oracle identity and its strength prospectively rather than inheriting P2's historical unknowns.

## 9.4 Do not promote any P2 remediation from historical correlation

No current P2 result authorizes:

```text
automatic route promotion
automatic placement promotion
global server-first activation
remediation effectiveness claim
historical unknown reclassification
```

---

# 10. P3 entry gate

P3 may start only when all items below are explicit for the experiment being launched.

## 10.1 Treatment isolation

Baseline and treatment must differ only in the intended placement dimension:

```text
A = LOCAL_FIRST_V1
B = SERVER_FIRST_DETERMINISTIC_V1
```

Keep equivalent:

```text
task semantics
exact source snapshot
acceptance oracle
controller class
proof policy
risk policy
required environment
public tool contract
```

## 10.2 Eligible first cohort

Use only tasks with:

```text
read-only or deterministic validation
portable environment
no GUI/device/secret affinity
strong oracle with explicit oracle_id
exact source snapshot / fingerprint
safe local fallback
```

Prefer HEAVY tasks only where remote placement can plausibly exceed transfer/setup overhead.

Feature work is a high rework-leverage stratum from P2, but it enters P3 only when it also satisfies these eligibility requirements.

## 10.3 Required enrollment / outcome evidence

Every experimental run must explicitly carry the already-defined P1 measurement identity where applicable:

```text
pair_id
policy
policy_version
provenance
replicate_id
task_class
environment_id
oracle_id
cache_stratum
order_index
trace/session identity as applicable
```

Controller timing/token/cost fields are populated only when genuinely observable; missing values remain unknown.

Quality outcome must be explicit; lifecycle `accepted` alone is not a post-accept quality outcome.

## 10.4 Primary P3 pilot metrics

```text
accepted rate
first-pass rate
TTAR
repair probability
```

Secondary:

```text
queue_ms
transfer_ms
execution_ms
proof_ms
local_cpu_minutes
local_heavy_minutes
remote_compute_minutes
fallback rate
source/proof mismatch count
placement regret where comparable
```

## 10.5 Pilot interpretation

Initial target remains 10–20 representative pairs for:

```text
instrumentation validation
variance estimation
break-even estimation
failure-mode discovery
power planning
```

Do **not** use 10 pairs as confirmatory production proof merely because a governance threshold says `min_pairs=10` elsewhere.

## 10.6 P3 promotion remains class-specific

No broad promotion unless:

```text
quality non-inferiority passes
source/authority/proof identity remains exact
TTAR or CAR is materially better
OR local burden is materially lower with acceptable TTAR
fallback is demonstrated
sample diversity is sufficient
analysis is powered for the intended claim
```

---

# 11. P2 closure matrix

| Question | P2 answer | Status before P3 |
|---|---|---|
| Is rework economically material? | Yes; repaired p50 ~4.82x first-pass in current accepted cohort | CLOSED |
| Which workflow has the largest observed repair burden? | Feature: 52/121 repaired accepted and 100/220 replans | CLOSED as observational finding |
| Is scope measurable? | Yes where `context_prepared.selected_paths` exists; unknown retained | CLOSED with missingness |
| Is oracle strength sufficient to explain workflow differences? | No; historical coverage is sparse | Explicit limitation |
| Are repair causes fully classified? | No; 118 structured events remain conservatively unclassified, led by 71 `CHECK_FAILED` | Explicit limitation, not fabricated |
| Is patch preflight observed working as a guardrail? | Yes; 70 known no-write failures stopped pre-run | Direct guardrail evidence |
| Is patch preflight's accepted-result causal effect known? | No | HOLD |
| Is exact-source causal effect known? | No | HOLD |
| Is semantic-localization causal effect known? | No | HOLD |
| Is recovery-fencing causal effect known? | No | HOLD |
| Is solution minimization a P2 treatment? | No | NOT ACTIVE |
| Is P2 implementation proven? | Yes | CHECKPOINTED |
| Is P3 allowed to reuse P2 accepted-only cohort as treatment denominator? | No | FORBIDDEN |
| Is automatic route/placement promotion authorized? | No | HOLD |
| Can P3 begin after its manifest/enrollment/oracle gate is frozen? | Yes | READY FOR CONTROLLED PILOT |

---

# 12. What does not need to be added before P3

Do not delay P3 to:

- invent historical oracle labels for unknown runs;
- force all 71 `CHECK_FAILED` events into a causal category;
- build a second analytics database;
- add a public MCP tool for P2 metrics;
- redesign EOCL/authority;
- enable Mini/Luna/Terra automatically;
- globally enable server-first;
- expand LSP concurrency;
- add arbitrary utility weights to create scalar regret;
- backfill cost, quality, or intervention epoch values that were never observed.

Those actions would reduce evidence quality rather than improve P2 closure.

---

# 13. Required P3 launch record

Before P3 starts, create/freeze one experiment manifest that contains at least:

```yaml
experiment_id:
hypothesis:
baseline_policy: LOCAL_FIRST_V1
treatment_policy: SERVER_FIRST_DETERMINISTIC_V1
policy_version:
activation_epoch:
task_sampling_frame:
eligibility:
  portable_environment: true
  no_gui_device_secret_affinity: true
  exact_source_required: true
  strong_oracle_required: true
primary_metrics:
  - accepted
  - first_pass
  - TTAR
  - repair
secondary_metrics:
  - queue_ms
  - transfer_ms
  - execution_ms
  - proof_ms
  - local_cpu_minutes
  - local_heavy_minutes
  - remote_compute_minutes
  - fallback
quality_floor:
cache_policy:
missing_data_policy:
assignment:
order_randomization:
analysis_script_sha:
promotion_gate:
stop_rule:
```

The manifest identity must be frozen before treatment outcomes are inspected.

---

# 14. Final phase boundary

```text
P1 measurement integrity        CLOSED
P2 rework diagnosis             CLOSED / ACCEPTED / CHECKPOINTED
P2 causal remediation efficacy  NOT PROVEN; HOLD
P3 experiment readiness         READY SUBJECT TO FROZEN MANIFEST / ENROLLMENT GATE
P3 execution                    NOT STARTED
```

**Next critical action:** create/freeze the P3 server-first paired-experiment manifest and only then launch the first bounded instrumentation pair. Do not change placement globally and do not infer P3 treatment efficacy from P2 historical data.

---

**End of P2 closure and P3 handoff.**

---

# 15. Final pre-P3 update after P0/P1/P2 remediation

**Fresh P1/P2 capture:** `2026-08-17T19:29:22.080878Z` (~02:29 ICT, 2026-08-18)

This section supersedes only the **current readiness status** above; the prior P2 snapshots remain valid dated evidence.

## 15.1 P0 source remediation is now a hard P3 activation gate

The intermittent TaskGroup/ExceptionGroup boundary has a durable source fix:

```text
run_id            cbffed4e2bee4ff4af90a43708407d3d
wave_id           adf0bbcb34844192adcaef633f655db8
state             CHECKPOINTED
accepted_at       2026-08-17T19:18:21.812Z
integrity         40 / 40 OK
proof fingerprint 981220b6988f838a239f513bf62d957e06a706b25563ec500459ac114575e10b
```

`Runtime.call_tool()` now prevents raw exception groups from escaping the tool boundary. A single typed child preserves its causal identity; mixed/multi-child groups become `ASYNC_TASK_GROUP_FAILED` with bounded child evidence.

The source fix has **not** been implicitly activated by restarting the currently running Runtime. Therefore P3 may not start until an explicit lifecycle restart loads this source and a live smoke proves:

```text
new process/server instance identity
workspace_context(detail=full) PASS
agent_workflow prepare PASS
no raw ExceptionGroup transport leakage
smart-v3 public tools = 8
```

## 15.2 P1 measurement plumbing smoke is now observed

Two synthetic pairs / four read-only runs were completed and checkpointed; all four have explicit quality outcomes. They exist only to validate measurement plumbing and are excluded from representative efficacy/regret evidence.

```text
pair IDs                   2
pair-tagged synthetic runs 4
controller observed         4 / 4
controller started_at       4 / 4
controller source           4 / 4 client_reported
token usage observed        0 / 4
monetary cost observed      0 / 4
quality outcomes            4 / 4
experimental quality rate   1.0
representative regret rows  0
```

Economics therefore remains:

```text
promotion_economics = HOLD
reason              = controller_cost_coverage_incomplete
```

This is the correct result. The smoke demonstrates that enrollment/controller-start/quality fields survive end-to-end; it does not invent token/cost telemetry and it cannot promote a policy.

Host-correlation at the same capture:

```text
host spans total                  55
bound host spans                  19
historical binding rate           34.5455%
causally eligible host runs        3
eligible runs with exact span      2
causal eligible-run coverage       66.6667%
```

`2/3` is an instrumentation signal with tiny N, not a production KPI.

## 15.3 P2 final readiness coverage is now explicit

Final readiness reporting wave:

```text
run_id            16c46b4098d14cfba2207226a3ad650f
wave_id           50dc3fd12732494d9597e08b8ee5dd74
state             CHECKPOINTED
accepted_at       2026-08-17T19:28:14.054Z
proof fingerprint f886182e40ff200f5254821570e7468e9c162bfd294c7859e0e64fcd8944a25f
```

It adds aggregate readiness metrics without reclassifying ambiguous failures or imputing unknown oracle values:

```text
representative/model-free accepted runs 330
failure events on repaired runs         223
mapped causal events                    105
unclassified events                     118
mapped causal coverage                  47.0852%
largest unclassified class              CHECK_FAILED = 71

oracle-eligible runs                    330
oracle observed                          57
oracle strong                             2
oracle not strong                        55
oracle unknown                          273
oracle observation coverage             17.2727%
```

These values clarify the two remaining P2 limitations:

1. causal repair classification is useful but still incomplete;
2. historical oracle-strength telemetry is far too sparse for a causal explanation of workflow differences.

Neither limitation requires inventing historical labels before P3. Instead, P3 must capture exact typed failure/oracle evidence prospectively.

Current feature hotspot is now:

```text
feature n          102
first-pass          50 = 49.0196%
repaired            52 = 50.9804%
replans            100
oracle observed       3
oracle unknown       99
first-pass p50    44.724 s
repaired p50     253.123 s
```

Current organic/model-free aggregate:

```text
accepted 330
first-pass 209 = 63.3333%
repaired 121 = 36.6667%
first-pass p50 52.875 s
repaired p50 251.271 s
repair median multiplier 4.75217x
```

## 15.4 P2 intervention verdict remains HOLD

No historical countermeasure now earns a causal-effect claim:

```text
patch_preflight        HOLD / not causally estimable
workdir_resolution     HOLD / not causally estimable
semantic_localization  HOLD / not causally estimable
exact_source           HOLD / not causally estimable
recovery_fencing       HOLD / not causally estimable
```

Patch preflight still has direct guardrail evidence (`70` known no-write failures stopped pre-run). That does not imply a measured percentage reduction in accepted-result rework.

## 15.5 Updated P3 entry gate

P3 execution is still `NOT STARTED`. Before its first representative pair:

1. explicitly restart/activate Runtime so the P0 source fix is live and prove the new instance;
2. freeze the P3 experiment manifest before outcomes are observed;
3. use intention-to-treat representative enrollment and preserve all assigned outcomes, not the P2 accepted-only denominator;
4. require exact source/task/oracle/environment identity and explicit strong-oracle evidence;
5. preserve controller token/cost missingness. If monetary cost is unavailable, CAR/cost promotion claims are forbidden;
6. record explicit quality outcome for each assigned replicate according to the study contract;
7. keep automatic placement/model promotion disabled;
8. treat the initial 10–20 representative pairs as instrumentation/variance/break-even pilot evidence, then power-size any confirmatory cohort.

Final status:

```text
P0 source fix                         CLOSED / CHECKPOINTED
P0 live activation                    REQUIRED BEFORE P3
P1 synthetic plumbing                 PASS
P1 representative efficacy            NOT PROVEN
P1 controller economics               HOLD
P2 diagnostic/readiness               CLOSED / CHECKPOINTED
P2 remediation efficacy               HOLD / NOT PROVEN
P3                                    NOT STARTED
```

---

**End of final pre-P3 P0/P1/P2 handoff update.**