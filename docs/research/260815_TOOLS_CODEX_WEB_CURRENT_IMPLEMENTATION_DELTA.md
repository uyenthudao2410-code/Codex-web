# Tools-Codex-web — Current Implementation Delta

**Observed date:** 2026-08-15  
**Repository:** `uyenthudao2410-code/Tools-Codex-web`  
**Branch:** `main`  
**Implementation evidence baseline:** `2592b7b0fed7aabd04260ceb3bcbf53f82f81399`  
**Desktop:** `web-mcp-assistant 0.3.4`  
**Public MCP profile:** `smart-v3`, exactly 8 public tools  
**Purpose:** authoritative current-status delta. Historical audit snapshots remain historical evidence. Documentation-only commits may advance branch HEAD without changing the implementation baseline or the product behavior described here.

---

## 1. Executive status

### P1 — COMPLETE / FULL LIVE PASS

Organic ChatWeb host-turn identity is explicitly correlated to the exact EOCL run without prompt/response content, timestamp proximity, latest-run inference, or cross-clock causality inference.

### P2 — COMPLETE

The P2 engineering/evidence-substrate phase is closed on the current implementation baseline:

```text
P2A current-policy idempotency                  COMPLETE / LIVE PASS
P2B source-fenced continuation + result tail    COMPLETE / LIVE PASS
P2C proof-cache opportunity truth               COMPLETE
P2D exact-source provenance + package hygiene   COMPLETE
operational stale authority debt                0 unresolved after canonical reconciliation
public Smart-v3 surface                         8 tools / unchanged
```

P2 completion means the reliability, source-fencing, measurement and provenance primitives are implemented, activated where activation is meaningful, and protected by deterministic proof. It does **not** mean future performance policy may be promoted without representative evidence.

The following are deliberately moved out of P2 and remain later-phase gates:

```text
Mini/Luna routing promotion        P4 representative paired accepted work
proof-cache performance promotion  P4/P5 representative opportunity/economics window
auto-handoff promotion             P4 representative A/B accepted work
Call Hierarchy                     P3 semantic activation first, then P4 experiment
independent GitHub release CI      external release-evidence gate
```

Current next critical engineering phase is **P3 native semantic live activation**, but it remains blocked by a real trusted binding prerequisite rather than missing P2 source code.

---

## 2. Exact implementation and delivery baseline

The P2 implementation evidence is bound to:

```text
implementation SHA: 2592b7b0fed7aabd04260ceb3bcbf53f82f81399
branch:             main
remote history:     origin/main contains this implementation commit
```

Documentation-only synchronization commits after this SHA do not alter the implementation evidence, runtime behavior, public tool contract, or validation results recorded below. A later product/source commit must explicitly advance the implementation baseline.

Relevant accepted/pushed implementation closures:

```text
fda89e48  Attest EOCL results in controlled replay
9262ff6a  Report proof-cache opportunity from EOCL
2592b7b0  Harden packaged resource sanitation
```

No P2 closure introduced a ninth public tool.

---

## 3. P1 host-turn → exact EOCL correlation — FULL LIVE PASS

The P1 measurement bridge remains closed and organically proven:

- Electron host observation schema v5 carries content-free `turn_id` + `trace_id` across the visible turn and host span.
- A new EOCL run may claim that identity exactly once.
- Existing/resumed runs do not claim a later turn.
- Controlled evaluation identity has explicit precedence.
- Electron journals/submits only an exact run/wave binding.
- The evaluator reports explicit host↔run linkage only when current-schema host journal evidence and EOCL observation agree on the exact content-free identity.

Host-visible duration remains host-visible evidence, not model inference latency.

---

## 4. P2A — Current-policy idempotency: COMPLETE / LIVE PASS

### Semantics

`task_epoch_v1` is the current policy epoch. Required durable operations use stable replay identity; optional intentional repeats remain possible.

Proven invariants include:

```text
same key + same semantic request       -> replay/deduplicate, no second side effect
same key + conflicting request         -> fail closed
previous-process unknown outcome       -> fail closed, never treated as safe pre-start
controller/fencing identity changes    -> no stale authority key collision
optional operations                    -> not silently converted to required deduplication
```

A live same-key canary on the active Runtime returned `deduplicated=true` with the original run/wave identity and no second mutation.

### Current activation sample

Direct current-runtime activation projection during P2 closure:

```text
policy epoch:             task_epoch_v1
required calls:           16
required keyed:           16
required coverage:        100.0%
configured target:        95.0%
coverage gate:            PASS
agent_workflow execute:   10 / 10 keyed
task_control accept:       4 / 4 keyed
task_control reject:       2 / 2 keyed
```

The count is reported explicitly; historical cumulative denominators are not substituted for the current-policy gate.

### Closure proof

Focused P2 regression boundary on current HEAD:

```text
30 passed
81 deselected
2 subtests passed
```

This set covers idempotency fault semantics together with P2 continuation/proof-cache activation boundaries.

---

## 5. P2B — Source-fenced continuation + result-tail semantics: COMPLETE / LIVE PASS

Continuation remains internal to the existing `agent_workflow`/git evidence path.

The signed continuation identity binds at least:

```text
base/source identity
worktree fingerprint
diff/content identity
scope / paths
relevant options
byte position
schema/version
```

Hard behavior:

```text
same source + same scope/options -> continuation proceeds
source drift                     -> fail closed
scope drift                      -> CONTINUATION_SCOPE_MISMATCH
options drift                    -> fail closed
signature/canonical tamper       -> fail closed
retry/reread                     -> allowed but explicitly measured as reread
mixed-source pages               -> forbidden
```

The public `agent_workflow phase=resume` path forwards explicit caller `paths` into the existing validator, so wrapper-level scope drift cannot be silently ignored.

A post-restart live canary previously proved successful same-scope continuation and public-wrapper scope mismatch rejection. Current source validation re-proved the same invariants; the continuation implementation bytes have not changed since that live proof.

Representative large-result ROI remains a later experiment. P2 does not manufacture a synthetic large corpus merely to inflate continuation counters.

---

## 6. P2C — Proof-cache opportunity truth: COMPLETE

Commit `9262ff6a` added a canonical bounded, content-free EOCL opportunity projection.

It reports:

```text
eligible / hits / misses / hit rate
stage_id + stage_version
miss reason / fingerprint-change class
saved_ms + completeness
accepted-run relation
accepted-checkpoint relation
bounded stage rows
```

It does not expose raw input fingerprints, source proof IDs, objectives, prompts, source content, credentials, or chain-of-thought.

### Current closure observation

Direct ledger projection during P2 closure:

```text
eligible opportunities:                  197
hits:                                      3
misses:                                  194
hit rate:                              1.5228%
miss: input fingerprint changed:          117
miss: cold:                                77
known saved_ms:                          8814
saved_ms completeness:                   true
runs with opportunities:                  107
accepted runs with opportunities:          81
accepted-checkpoint opportunities:        150
accepted-checkpoint hits:                   2
```

This is sufficient to close the **opportunity-measurement phase**, not to claim proof-cache is a production performance winner.

Current policy is intentionally:

```text
exact proof identity / fingerprint truth  KEEP
reuse correctness semantics               KEEP
performance-policy promotion              HOLD for representative window
fingerprint weakening to chase hit-rate   FORBIDDEN
```

That promotion decision belongs to P4/P5 evidence/simplification, not P2 implementation.

---

## 7. P2D — Exact-source Windows provenance: COMPLETE

The Windows release/provenance flow distinguishes development smoke from publishable release evidence and binds candidate identity to exact source/build information.

The release sidecar/gates cover the relevant identity classes, including exact Git source state, application/MCP/native identities, artifact hashes and canonical proof identity. Publishability fails closed when exact-source requirements are not met.

Focused current-HEAD Node proof for provenance and packaged-resource validation passed together with `git diff --check`.

Independent CI is still required before calling a candidate independently release-proven; that external release gate is tracked separately in Section 10.

---

## 8. P2D — Windows packaged-resource sanitation: COMPLETE / ACTUAL PACK PASS

Commit `2592b7b0` closes broad `extraResources` contamination risk with two layers:

1. pre-copy exclusions;
2. a Windows `afterPack` fail-closed scan over actual packaged resources.

Explicitly excluded classes include:

```text
coding-tools-mcp/benchmarks/reports/**
**/__pycache__/**
**/.pytest_cache/**
**/*.egg-info/**
**/.coding-tools/**
**/*.pyc
**/*.pyo
```

Actual package evidence on the implementation baseline:

```text
Windows unpacked electron-builder       PASS
afterPack validator                     PASS
independent packaged-tree entries       258
forbidden packaged paths                  0
tracked egg-info packaged                no
pytest cache packaged                    no
raw benchmark reports packaged          no
```

No dependency repair or local smoke artefact was committed as product source.

---

## 9. P2 operational authority hygiene — COMPLETE

P2 closure found 12 historical EOCL runs that were older than the configured 24-hour stale threshold and had no live ownership according to the canonical ledger predicate.

The ledger's own operator reconciliation API was used with `close_stale_active=true`; no SQLite row was manually edited or deleted.

The reconciliation path re-checks and protects live ownership from:

```text
live background operations
active/waiting agent lanes
non-expired write authority
non-expired controller fencing/lease
```

It retains run/wave/evidence history while terminalizing abandoned active lifecycle state.

Closure result:

```text
stale candidates before:              12
canonically reconciled:               12
stale candidates after:                0
unresolved_stale_orchestration_runs:   0
orphaned_background_operations:        0
orphaned_idempotency_records:           0
agent_lanes_waiting_after_restart:      0
```

The read-only audit run used to diagnose this debt was explicitly terminalized `ABORTED` after the audit completed; it was not left as new active debt.

---

## 10. Broad P2 acceptance boundary — PASS

Current source broad proof after stale reconciliation:

```text
npm run test:all                      EXIT 0
Node / Electron                       105 / 105 PASS
source-root-clean                     PASS
Python MCP                            314 PASS, 1 skipped
focused P2                            30 PASS + 2 subtests
provenance/package focused tests      PASS
git diff --check                      PASS (runtime-state line-ending warning only)
```

The broad Python boundary includes idempotency, evaluation replay/report, Execution Hub, orchestration ledger/control/workflow, runtime activation, task/build, universal idempotency, resilience, provider/routing and semantic fallback tests.

No production route threshold, auto-handoff policy, permission authority, or public tool surface was loosened to obtain this result.

---

## 11. Exact-implementation-SHA GitHub Actions — EXTERNAL RELEASE GATE

GitHub Actions run `31882079363` is bound to the implementation evidence baseline:

```text
2592b7b0fed7aabd04260ceb3bcbf53f82f81399
```

Both required jobs were marked `failure`, but:

```text
runner_id:   0
runner_name: empty
steps:       []
```

GitHub's annotation says the jobs were not started because recent account payments failed or the spending limit needs to be increased.

Classification:

```text
external account/billing pre-run gate
not source-regression evidence
not independent green CI proof
```

This blocks an independent GitHub release-proof claim, but it does not reopen P2 implementation/reliability completion. Do not burn reruns while the account prerequisite is unchanged.

---

## 12. PerformanceTrace operation-boundary wall time — SOURCE COMPLETE

Current implementation captures wall timestamps at operation entry/exit while monotonic duration remains authoritative:

```text
entry -> started_wall_utc + monotonic start
exit  -> finished_wall_utc + monotonic end
```

Existing tests assert `wall_time_source = operation_boundary`.

Older audit text describing record-time pseudo-timestamps is stale for current source.

---

## 13. P3 — Native semantic live activation: BLOCKED BY REAL PREREQUISITE

The Python ↔ Rust semantic boundary is source-ready, read-only, bounded, workspace/project scoped and fail-closed in focused tests.

Live runtime currently reports:

```text
NATIVE_LSP_BINDING_NOT_CONFIGURED
missing trusted origin binding
missing credential-file binding
```

Do not invent endpoint URL, project credential, token or grant. Do not weaken loopback/project/workspace authorization. Text fallback is not live semantic evidence.

Once a real trusted binding exists, P3 activation acceptance should require authenticated/project-bound success, negative auth/workspace/path cases, read-only behavior, bounded responses, deterministic fallback and nonzero real semantic attempted/handled evidence.

Call Hierarchy remains downstream of that activation.

---

## 14. P4 — Representative routing/handoff experiments: EVIDENCE PENDING

The controlled replay machinery is ready to collect scientifically valid paired route evidence. It does not infer acceptance from process exit code: accepted trials require authoritative EOCL run/checkpoint/proof/oracle evidence and pair-level source identity equality.

What is still required is real accepted work with the same:

```text
task semantics
exact source/base
environment
acceptance oracle
controlled cache/thread stratum where material
```

Current policy remains:

```text
deterministic-first
automatic routing activation   OFF
Mini/Luna                      explicit bounded study/candidate lanes
Terra                          shadow / explicit
auto-handoff                   OFF
synthetic/no-op pair inflation forbidden
```

These gates are no longer P2 blockers.

---

## 15. P5 — Promotion and simplification: NOT STARTED AS POLICY PROMOTION

After representative P4 evidence, each accelerator should be classified:

```text
KEEP
KEEP BUT DEMOTE CLAIM
FIX
REMOVE
DEFER
```

Examples:

- continuation: retain correctness/source fence regardless; promote performance claims only with representative tail benefit;
- proof cache: retain exact reuse semantics, possibly demote performance expectations if opportunity remains low;
- Mini/Luna routing: promote only on accepted-result economics/quality/TTA evidence;
- auto-handoff: enable only if representative A/B shows continuity benefit without duplicate/state-loss regression;
- Call Hierarchy: keep only if post-P3 qualified cross-file workloads benefit.

---

## 16. Code Mode arbitrary generated-code execution — HOLD / FAIL-CLOSED

The model-hidden read-only host-binding prerequisite exists, but no current worker backend proves the full isolation contract required for arbitrary generated code.

A qualifying backend must prove all of:

```text
no_direct_filesystem
no_network
no_inherited_environment_secrets
no_unrestricted_subprocess
bounded_framed_host_binding_only_ipc
```

Do not enable Code Mode using Python `exec/eval`, Node VM/worker threads, unrestricted subprocesses, Job Object alone, or partial existing sandbox controls.

---

## 17. Optional / demand-driven follow-ups

These remain off the critical path until real product/benchmark demand appears:

```text
focused Go validation
structured file delete
webcodex disconnect
generic ArtifactRef / Composite Read expansion
semantic parallel-proof scheduling
dedicated push transport
authenticated remote-phone status
other upstream convenience capabilities
```

Do not build them merely to reduce a roadmap checklist.

---

## 18. Current completion assessment

```text
P1 host-turn ↔ EOCL correlation                  FULL LIVE PASS
P2 overall                                       COMPLETE
  P2A idempotency                                COMPLETE / LIVE PASS
  P2B source-fenced continuation                 COMPLETE / LIVE PASS
  P2C proof-cache opportunity measurement        COMPLETE
  P2D provenance + package sanitation            COMPLETE / ACTUAL PACK PASS
P2 unresolved stale authority                    0
local Node/Electron boundary                     105 / 105 PASS
local Python MCP boundary                        314 PASS, 1 skipped
implementation-SHA GitHub CI                      EXTERNAL BILLING GATE / NO RUNNER
P3 native semantic live activation               BLOCKED / REAL BINDING REQUIRED
P4 paired routing promotion                       REPRESENTATIVE EVIDENCE PENDING
P4 auto-handoff                                  REPRESENTATIVE A/B PENDING
P4/P5 proof-cache performance policy             REPRESENTATIVE WINDOW PENDING
P4 Call Hierarchy                                HOLD behind P3 activation
Code Mode isolated arbitrary execution            HOLD / SECURITY BACKEND REQUIRED
public Smart-v3 tool count                        8 / UNCHANGED
```

There is no known P2 source/activation/operational blocker left.

---

## 19. Next-action policy

With P2 closed, resume in this order:

1. **P3 trusted semantic binding becomes available** → controlled live semantic activation and security/fallback canary.
2. **GitHub billing/account prerequisite is corrected** → obtain independent Linux + Windows exact-implementation-SHA CI with actual runner allocation/steps.
3. **Representative real tasks naturally arrive** → collect source-matched Mini/Luna routing pairs and handoff A/B evidence; do not manufacture samples.
4. **Representative proof-cache window is sufficient** → make a P5 keep/demote/fix/remove/defer decision without weakening exact proof identity.
5. **Qualified semantic cross-file workloads exist after P3** → run bounded Call Hierarchy experiment.
6. **A product requirement justifies optional work** → select the smallest evidence-backed item rather than generically expanding framework surface.

---

## 20. Operations in the P2 closure

```text
source implementation mutation in final closure: no
canonical stale-run reconciliation:             yes, 12 / 12 closed
manual SQLite editing/deletion:                  no
runtime/Electron restart in final closure:       no
provider paid call:                              no
route threshold change:                          no
auto-handoff enablement:                         no
public tool expansion:                           no
release/tag/deploy:                              no
```

The final P2 closure changed operational evidence state only through the canonical ledger reconciliation API and synchronized this authoritative status document. The implementation baseline remains `2592b7b0` until a later product/source commit changes behavior.
