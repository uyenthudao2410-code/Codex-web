# Tools-Codex-web — Current Implementation Delta

**Observed date:** 2026-08-15  
**Repository:** `uyenthudao2410-code/Tools-Codex-web`  
**Branch:** `main`  
**Implementation evidence baseline:** `2592b7b0fed7aabd04260ceb3bcbf53f82f81399`  
**Desktop:** `web-mcp-assistant 0.3.4`  
**Public MCP profile:** `smart-v3`, exactly 8 public tools  
**Purpose:** authoritative current-status delta only. Historical audit snapshots remain historical evidence and are not rewritten by this document. Documentation-only synchronization commits may advance the branch beyond the implementation evidence baseline without changing the product behavior described here.

---

## 1. Executive status

The current repository no longer has a known small P0/P1 source implementation blocker that can be responsibly closed without an external prerequisite or representative accepted-work evidence.

The correct current state is:

```text
core reliability / measurement source work    source-complete + locally proven
exact-implementation-SHA GitHub CI             externally blocked before runner allocation
native semantic live activation                blocked by real binding prerequisite
routing / auto-handoff promotion               representative evidence pending
proof-cache policy simplification              representative window pending
Call Hierarchy                                 blocked behind semantic activation/workload
Code Mode arbitrary generated-code execution   fail-closed HOLD pending a qualifying isolation backend
optional convenience features                  demand-driven / deferred
```

Do not create synthetic workload, weaken proof identities, invent provider/semantic credentials, or add public tools merely to make roadmap counters nonzero.

---

## 2. Exact implementation and delivery baseline

The product implementation evidence in this document is bound to:

```text
implementation SHA: 2592b7b0fed7aabd04260ceb3bcbf53f82f81399
branch:             main
remote history:     origin/main contains this implementation commit
```

Documentation-only synchronization commits after this SHA do not alter the implementation evidence, runtime behavior, public tool contract, or validation results recorded below. When a later product/source commit changes implementation behavior, this baseline must be advanced explicitly rather than inferred from the latest documentation commit.

Recent accepted/pushed implementation closures in this continuation:

```text
fda89e48  Attest EOCL results in controlled replay
9262ff6a  Report proof-cache opportunity from EOCL
2592b7b0  Harden packaged resource sanitation
```

No public Smart-v3 expansion was introduced; the model-facing surface remains exactly 8 tools.

---

## 3. P1 organic host-turn → exact EOCL correlation — LIVE PASS

The remaining source/runtime measurement bridge is closed and organically proven:

- Electron host observation schema v5 carries content-free `turn_id` + `trace_id` across user-visible turn, first assistant-visible response and host span.
- A new EOCL run can claim that identity exactly once; correlation does not use timestamp proximity, “latest run”, current-thread inference, prompt text or response text.
- The exact host span is submitted as `task_control observation` with explicit run/wave identity.
- Evaluation reports explicit host↔run linkage only when journal and EOCL observation identities agree.
- Organic live evidence has produced `explicit_host_span_count >= 1` with a complete causal run.

Host-visible duration remains host-visible evidence; it is not re-labeled as model inference latency.

---

## 4. Reliability / transport closures

### 4.1 Current-policy idempotency — LIVE CANARY PASS

A same-key mutation-safe canary demonstrated durable replay rather than re-execution:

```text
same idempotency key + same request -> deduplicated=true
run_id / wave_id                    -> preserved
new source mutation                 -> none
```

The observed post-restart current-policy sample reached full required-key coverage for the small live sample used in the canary. This does not authorize weakening idempotency semantics or backfilling historical counters.

### 4.2 Source-fenced continuation — PASS

The internal continuation path is source/worktree and scope/options fenced. Correct continuation works; mismatched/stale scope fails closed. The capability remains internal to `agent_workflow`; no ninth public tool was added.

Representative large-result ROI remains a measurement question, not an implementation blocker.

### 4.3 Controlled replay causal acceptance — PASS

Controlled replay now refuses to call a trial accepted merely because its process exited successfully. A trial is attestable only when its isolated EOCL ledger contains exactly one matching accepted run with:

- matching pair/policy/replicate/order identity;
- matching task/source/oracle/runtime identity;
- the expected resolved route for the policy;
- accepted checkpoint plus proof/oracle evidence.

A paired study reports complete accepted-result evidence only when both arms also share the same EOCL pair fingerprint/source identity.

Synthetic/no-op trials are not promoted into representative routing evidence.

---

## 5. Wave 2C proof-cache opportunity truth — SOURCE + PROOF COMPLETE

Commit `9262ff6a` adds a canonical, bounded, content-free EOCL projection for proof-cache opportunity analysis.

It reports:

```text
eligible / hits / misses / hit-rate
stage_id + stage_version grouping
miss-reason / fingerprint-change class
saved_ms + saved_ms completeness
accepted-run relation
accepted-checkpoint relation
bounded stage rows
```

It deliberately does **not** project raw input fingerprints, source proof IDs, objectives, prompts, source content or credentials.

Validation boundary:

```text
focused proof-cache / ledger / runtime tests   37 / 37 PASS
direct runtime_activation CLI                 PASS
full Python MCP suite                         314 PASS, 1 skipped, 20 subtests PASS
git diff --check                              PASS
```

A live mixed historical ledger observation after the projection was introduced showed:

```text
eligible opportunities  196
hits                       3
misses                   193
hit rate               ~1.53%
known saved_ms           8814
saved_ms completeness    complete for observed hits
```

These numbers are **opportunity truth, not causal promotion evidence**. The window is not proven representative-only, so it must not be used to broaden fingerprints, auto-promote cache policy, or market proof-cache as a performance winner.

Current decision:

```text
exact reuse semantics          KEEP
performance-policy promotion   HOLD
simplification/demotion choice AFTER representative window
```

---

## 6. PerformanceTrace wall-time truth — SOURCE COMPLETE

The older audit statement that PerformanceTrace materializes both wall timestamps at record-time is stale for the current source.

Current implementation captures:

```text
operation entry -> started_wall_utc + monotonic start
operation exit  -> finished_wall_utc + monotonic end
```

Monotonic duration remains authoritative. Existing tests assert `wall_time_source = operation_boundary`.

Do not re-open this as a P0 source defect unless new evidence demonstrates regression.

---

## 7. Exact-source Windows release provenance — SOURCE COMPLETE

Current Windows release/provenance flow has exact-source guards and sidecar identity sufficient to distinguish development smoke from publishable release evidence, including source/build identity and content hashes.

Release policy still requires independent exact-SHA proof before calling a candidate release-proven. A local successful build is not a substitute for GitHub/canonical independent CI when that gate is required.

---

## 8. Windows packaged-resource sanitation — SOURCE + ACTUAL PACK PROOF COMPLETE

Commit `2592b7b0` closes the broad `extraResources` contamination risk with two layers:

1. pre-copy exclusions for known volatile/raw artefacts;
2. a Windows `afterPack` fail-closed validator over the actual packaged resources tree.

The package excludes:

```text
coding-tools-mcp/benchmarks/reports/**
**/__pycache__/**
**/.pytest_cache/**
**/*.egg-info/**
**/.coding-tools/**
**/*.pyc
**/*.pyo
```

The afterPack validator rejects any forbidden path that survives filtering and reads path metadata only; it does not inspect user/source file contents.

Evidence on exact implementation source before commit/push:

```text
focused packaging/config validator tests     PASS
actual Windows unpacked electron-builder      PASS
afterPack hook                                executed without violation
independent packaged-tree scan               258 entries scanned
forbidden packaged paths                       0
tracked egg-info in packaged tree              absent
pytest cache in packaged tree                  absent
raw benchmark reports in packaged tree         absent
Node / Electron full suite                    105 / 105 PASS
source-root-clean check                        PASS
Python MCP full suite                         314 PASS, 1 skipped
git diff --check                              PASS
```

The local dependency tree needed repair after an interrupted `npm ci` encountered a running-Electron file lock; no runtime/Electron process was killed or restarted to bypass that lock, and no dependency repair was committed as source.

---

## 9. Exact-implementation-SHA GitHub Actions truth — EXTERNALLY BLOCKED, NOT SOURCE FAILURE

GitHub Actions run `31882079363` is bound exactly to the implementation evidence baseline:

```text
2592b7b0fed7aabd04260ceb3bcbf53f82f81399
```

The workflow has two required jobs:

```text
test          ubuntu-latest
test-windows  windows-latest
```

Both jobs completed as `failure`, but the runner evidence is:

```text
runner_id:   0
runner_name: empty
steps:       []
```

GitHub's check annotation states that the jobs were **not started** because recent account payments failed or the spending limit needs to be increased.

Therefore:

```text
classification = external account/billing pre-run gate
source test regression evidence = none from this workflow run
independent exact-SHA green CI  = still unavailable
```

Do **not** rerun repeatedly while the billing/spending prerequisite is unchanged. Do **not** call local PASS equivalent to independent GitHub CI. Once the account prerequisite is corrected, rerun or allow a later implementation SHA workflow to execute real steps and classify its result normally.

Documentation-only commits do not repair or invalidate this CI result because the product implementation evidence remains bound to `2592b7b0` until a later implementation commit is introduced.

---

## 10. Native semantic live activation — BLOCKED BY REAL PREREQUISITE

The Python ↔ Rust semantic boundary is source-ready, read-only, bounded, workspace/project scoped and fail-closed in focused tests.

Live activation remains unavailable with:

```text
NATIVE_LSP_BINDING_NOT_CONFIGURED
```

The current runtime is missing the trusted native semantic origin/credential binding required by the existing design.

Rules:

- do not invent endpoint URL, project credential, grant or token;
- do not weaken loopback/project/workspace authorization;
- do not treat text fallback as live semantic evidence;
- no runtime/Electron restart is justified until a real binding exists and activation is explicitly authorized.

Call Hierarchy remains downstream of this gate.

---

## 11. Routing calibration — REPRESENTATIVE EVIDENCE PENDING

The source now contains the machinery required to collect paired route evidence safely, including isolated replay, EOCL acceptance attestation and pair-source identity checks.

What is still missing is not another harness; it is real accepted work with:

```text
same task semantics
same exact base/source
same environment
same acceptance oracle
actual baseline route
actual candidate route
representative provenance
```

Current policy remains:

```text
deterministic-first
automatic_activation = false
Mini/Luna             bounded explicit candidates
Terra                 shadow / explicit
synthetic/no-op pair inflation = forbidden
```

Do not lower thresholds merely because the harness is now capable of producing valid pairs.

---

## 12. Auto-handoff — MECHANISM COMPLETE, A/B EVIDENCE PENDING

Durable capsule/resume, controller fencing and current handoff mechanics are source/fault proven.

The remaining gate is representative operational comparison:

```text
healthy same-thread continuation
vs
fresh durable-capsule resume
```

Measure accepted-result quality, missing/duplicate work, TTA, cost/cache and visible bytes where observable.

Current policy remains:

```text
healthy thread      -> continue same thread
rollover/recovery   -> durable capsule
auto handoff        -> OFF
```

Adding another synthetic handoff simulator would not close this gate.

---

## 13. Code Mode arbitrary generated-code execution — HOLD / FAIL-CLOSED

The model-hidden host-binding proxy prerequisite is source-ready and bounded to read-only operations, but no current worker backend proves the complete isolation contract required for arbitrary generated-code execution.

A qualifying backend must prove all of:

```text
no_direct_filesystem
no_network
no_inherited_environment_secrets
no_unrestricted_subprocess
bounded_framed_host_binding_only_ipc
```

Current Job Object / existing Landlock controls are not sufficient as that complete security boundary.

Do not enable Code Mode with Python `exec/eval`, Node VM/worker threads, unrestricted subprocesses, Job Object alone, or the current partial sandbox controls.

This is a deliberately fail-closed security prerequisite, not a small missing feature to implement opportunistically.

---

## 14. Optional / demand-driven follow-ups

The following remain intentionally off the critical path until real product/benchmark demand appears:

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

Do not build these merely to reduce a roadmap checklist.

---

## 15. Current completion assessment

```text
P1 host-turn ↔ EOCL correlation                  LIVE PASS
current-policy idempotency canary                LIVE PASS
controlled replay EOCL attestation               PASS
source-fenced continuation                       PASS
proof-cache opportunity projection               SOURCE + PROOF COMPLETE
PerformanceTrace operation-boundary wall time    SOURCE COMPLETE
exact-source Windows provenance                  SOURCE COMPLETE
Windows packaged-resource sanitation             SOURCE + ACTUAL PACK PASS
local full Node/Electron boundary                 105 / 105 PASS
local full Python MCP boundary                    314 PASS, 1 skipped
implementation-SHA GitHub CI                      EXTERNAL BILLING GATE / NO RUNNER
native semantic live activation                  BLOCKED / REAL BINDING REQUIRED
Call Hierarchy                                    HOLD behind semantic activation
paired routing promotion                          REPRESENTATIVE EVIDENCE PENDING
auto-handoff                                      REPRESENTATIVE A/B PENDING
proof-cache performance policy                    REPRESENTATIVE WINDOW PENDING
Code Mode isolated arbitrary execution            HOLD / SECURITY BACKEND REQUIRED
public Smart-v3 tool count                        8 / UNCHANGED
```

There is currently no known critical source implementation defect that should be filled with speculative code before those external/evidence gates move.

---

## 16. Next-action policy

When external state changes, resume in this order:

1. **GitHub billing/account prerequisite corrected** → obtain exact-implementation-SHA Linux + Windows CI where runners allocate and steps actually execute.
2. **Trusted native semantic binding available + activation authorized** → controlled live semantic activation and security/fallback canary; only then collect semantic workload.
3. **Representative real tasks naturally arrive** → collect source-matched Mini/Luna routing pairs and handoff A/B evidence; do not manufacture samples.
4. **Representative proof-cache window becomes large enough** → decide `KEEP`, `KEEP BUT DEMOTE CLAIM`, `FIX`, `REMOVE`, or `DEFER`; exact fingerprint truth remains invariant.
5. **Qualified semantic cross-file workloads exist** → run bounded Call Hierarchy experiment.
6. **A product requirement justifies optional P3 work** → select the smallest demand-backed item rather than expanding framework surface generically.

---

## 17. Operations in this continuation

```text
implementation commits pushed: yes
latest implementation SHA:     2592b7b0fed7aabd04260ceb3bcbf53f82f81399
documentation sync commits:    may advance branch HEAD without changing this implementation baseline
runtime/Electron restart:      no
provider paid call:            no
route threshold change:        no
auto-handoff enablement:       no
public tool expansion:         no
release/tag/deploy:            no
```

The correct next constraint is no longer “find another source feature.” It is to wait for the specific external or representative evidence required by the remaining gates, while keeping the already-proven source boundaries stable.
