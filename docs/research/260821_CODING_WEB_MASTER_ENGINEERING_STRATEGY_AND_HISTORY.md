# CODING WEB — MASTER ENGINEERING STRATEGY, IMPLEMENTATION STATE & HISTORICAL LEDGER

> **Canonical consolidated document**  
> **Effective date:** 2026-08-21  
> **Workspace:** `E:\DEV\Codex-web`  
> **Purpose:** one maintained engineering document for current implementation state, forward strategy, upstream-reuse policy, execution gates, and historical traceability.  
> **Supersedes and retires:**
> - `docs/research/260820_CODING_WEB_TECHNICAL_EVALUATION_AND_IMPLEMENTATION_PLAN.md`
> - `docs/research/260821_CODING_WEB_IMPLEMENTATION_CLOSURE.md`
> - `docs/research/260821_UPSTREAM_FIRST_REUSE_STRATEGY_AND_IMPLEMENTATION_PLAN.md`
>
> The retired documents are consolidated into this file so future work has **one research/engineering control document** rather than three partially overlapping sources. Their important history, status transitions, source identities, RUN/WAVE/proof identifiers, decisions, failures, lessons, and policy evolution are preserved below.
>
> This file does **not** replace repository-level maintained product truth such as `AGENTS.md`, `docs/CURRENT_STATE.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/TESTING.md`, security, release, or subsystem authority documents. When repository truth conflicts with this file, follow the precedence in §1.

---

# 0. Executive decision

Coding Web is no longer treated as a normal WebCodex fork and is no longer managed by a growing set of dated implementation plans.

The current product is a **Windows Electron Execution Hub + Recovery Host + one Coding Tools MCP Runtime**, with WebCodex/Rust/server/runner components retained where they are useful as foundations or subsystems.

The engineering program that created the current architecture is **source-engineering closed**. New work must not silently reopen previously accepted phases merely because a new upstream implementation appears or because a historical plan once listed something as future work.

From this document forward, four rules govern the project:

1. **Preserve current authority architecture.** EOCL, one-writer mutation, Recovery/Execution Hub ownership, current secret boundary, evidence lineage, and operator acceptance remain canonical.
2. **Reuse upstream implementation aggressively where compatible.** Copy code/tests before rewriting solved problems locally.
3. **Do not confuse historical state with current state.** Historical failed/replanned waves stay visible for audit, but they do not override later accepted source.
4. **Maintain one traceable engineering narrative.** Current state, future strategy, and historical evidence live in this file with explicit dates and identities.

The forward engineering doctrine is:

> **UPSTREAM-FIRST REUSE**  
> **Copy implementation whenever compatible.**  
> **Adapt boundaries, not algorithms.**  
> **Never copy a conflicting authority plane.**  
> **Never reimplement merely because Git histories diverged.**

Short form:

> **Reuse aggressively — integrate conservatively.**

Architecture shorthand:

> **Copy code, not authority.**

---

# 1. Authority, precedence, and non-retroactivity

## 1.1. Repository precedence

Use this order when sources disagree:

1. current implementation and authoritative focused/live proof for the exact checkout/process being operated;
2. `AGENTS.md`;
3. `docs/CURRENT_STATE.md`;
4. maintained architecture/security/release/testing/roadmap documents relevant to the subsystem;
5. this master engineering document;
6. durable EOCL reports and historical evidence for reconstructing past decisions;
7. old external notes, discussions, or archived copies.

For execution authority, **runtime EOCL state always governs what transition/write/proof action is legal next**.

## 1.2. Role of this document

This file answers four different questions in one place:

- **WHAT IS TRUE NOW?** — current engineering state and open gates;
- **HOW DO WE CHANGE IT?** — forward engineering/upstream-reuse method;
- **HOW DID WE GET HERE?** — historical S/W/P checkpoints and major incidents;
- **HOW DO WE AUDIT A CLAIM?** — trace procedure from decision -> run/wave -> proof -> source fingerprint -> current status.

## 1.3. Non-retroactivity rule

The upstream-first policy is **forward-looking**.

It does not retroactively invalidate accepted work simply because a different implementation could have been copied from upstream.

A previously closed workstream remains closed unless a new, explicit maintenance/reopen trigger exists:

- concrete defect;
- security/reliability fix;
- measurable performance/maintenance benefit;
- concrete consumer/product requirement;
- upstream change that materially affects already reused code;
- explicit operator architecture decision.

**Upstream parity alone is not a reopen trigger.**

## 1.4. Closed workstream versus maintenance wave

Correct model:

```text
W5 Context Compiler = CLOSED
        |
        +-- future upstream/local bugfix --> NEW MAINTENANCE WAVE
        |
        +-- measurable improvement ------> NEW MAINTENANCE WAVE
```

Incorrect model:

```text
upstream has better implementation
        -> reopen W5 as unfinished
```

The historical closure remains valid for the source/fingerprint that earned it.

## 1.5. Source identity rule

Any later source mutation creates a new source identity.

Past proof remains valid **historical evidence for the exact fingerprint it proved**, but it must not be reused as proof for materially changed source.

---

# 2. Current product truth

## 2.1. Operated topology

```text
ChatWeb / ChatGPT
      |
      | MCP over primary tunnel
      v
Recovery Host / Execution Hub authority
      |
      +--> ONE Coding Tools MCP Runtime
      |       |
      |       +--> workspace / Git / commands / proof / EOCL
      |       +--> artifact/context/semantic/runtime helpers
      |
      +--> Electron Execution Control Center
      |
      +--> independent Recovery MCP / Recovery Tunnel
      |
      +--> Codex Desktop thin client/proxy

Secondary provider/reasoning lanes:
  Codex App Server / OpenCode / candidate lanes
  -> bounded candidate, review, read-only, or explicitly authorized work
  -> never implicit peer authority over the canonical checkout
```

## 2.2. Canonical authority split

| Authority | Canonical owner |
|---|---|
| semantic coordination/final go-no-go in coordinated ChatWeb work | ChatWeb/Sol |
| lifecycle and trusted local host supervision | Electron / Recovery Host |
| workspace mutation, deterministic proof, orchestration ledger | Coding Tools MCP / EOCL |
| source write ownership | one active write lease only |
| secrets at trusted host boundary | Electron/Recovery Host + local Secret Broker boundary |
| durable execution history | EOCL/orchestration ledger |
| package/release publication | explicit separate release authority; not implied by source acceptance |

## 2.3. Public model-facing contract

`smart-v3` remains exactly eight public tools unless a future explicit product decision changes the contract:

```text
workspace_context
agent_workflow
task_control
document_workflow
exec_command
command_control
request_permissions
view_image
```

`restart_runtime` is an action of `task_control`, not a ninth tool.

## 2.4. Core philosophy

Coding Web is a **stateful coding operating layer**, not a loose collection of tools.

The design optimizes for:

- one canonical execution truth;
- multiple model/client entry points;
- deterministic mutation ownership;
- durable run/wave/proof state;
- source identity;
- explicit recovery semantics;
- compact model-facing context;
- measurable routing/economics;
- operator-visible control;
- minimal unique maintenance surface.

---

# 3. Current engineering closure status

## 3.1. Overall status

As reconciled on 2026-08-21:

- **ENGINEERING SOURCE CORE: CLOSED / ACCEPTED**
- **S1-S9: TERMINAL** — accepted implementation or explicit gate/defer
- **P0.3 Recovery: CLOSED / ACCEPTED**
- **P1.1 source: CLOSED / ACCEPTED**
- **P1.1 package content: BUILT / SMOKE-VERIFIED / HASH-VERIFIED**
- **P1.1 clean live provenance: PENDING LIVE ACTIVATION / RESTART REQUIRED**
- **P1.2 routing economics: EVIDENCE-GATED / KEEP DETERMINISTIC**
- **P1.3 automatic routing promotion: NO PROMOTION / GATE-CLOSED**
- **P2.1 native semantic/LSP: BLOCKED_CONFIG / TEXT FALLBACK RETAINED**
- **Final release acceptance: NOT CLAIMED**

There was no known hidden source implementation blocker at the accepted source fingerprint. The remaining immediate material boundary was operational activation of the accepted cross-session provenance fix in the resident runtime.

## 3.2. Accepted source identity at closure

```text
Baseline Git HEAD:
640ad37e3e571a0a56af376e9d3bda2b89bf0669

Accepted release-bearing source/worktree fingerprint:
48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e

smart-v3 contract SHA-256:
abd0f63f1653afc356a31d6c2cf23b21ddd01abdaee9d014f4ffa8ad98814a14
```

These identities are historical closure identities. Any later source change requires new proof.

## 3.3. Phase status S1-S9

| Phase | Terminal status | Meaning |
|---|---|---|
| S1 | **CLOSED** | baseline/control-plane foundations accepted |
| S2 | **CLOSED** | sparse/context execution foundations implemented; old W1 REPLAN superseded |
| S3 | **CLOSED with provider degradation explicit** | semantic source layer exists; native provider can degrade safely |
| S4 | **CLOSED / KEEP_SHADOW** | context/solution intelligence source exists; no automatic efficacy promotion |
| S5 | **CLOSED** | one-writer orchestration and mutation fencing accepted |
| S6 | **CLOSED with general-worker gate** | capability/secret foundation accepted; unsafe arbitrary worker remains fail-closed |
| S7 | **CLOSED** | trace/MCP2026/process lifecycle architecture accepted |
| S8 | **CLOSED as explicit defer** | Computer Use and remote device lease remain gate-closed |
| S9 | **CLOSED as shadow/defer** | shadow candidate path exists; external A2A remains gate-closed |

**Permanent control:** do not reopen S1-S9 just to add framework or match upstream feature count.

## 3.4. Workstream status W0-W15

| Workstream | Current terminal classification | Current meaning |
|---|---|---|
| W0 Baseline/control truth | **CLOSED** | fingerprints, EOCL evidence, proof/checkpoint discipline established |
| W1 Sparse projection | **CLOSED** | bounded/sparse execution behavior implemented and accepted |
| W2 Artifact bridge/import | **CLOSED** | artifact/reference/content-addressed boundaries present |
| W3 Attribution/provenance | **CLOSED** | caller/run/wave/proof attribution accepted and later hardened |
| W4 Semantic Repository Graph | **CLOSED / PROVIDER-DEGRADED ALLOWED** | source graph exists; fallback valid |
| W5 Context Compiler | **CLOSED / SHADOW-ONLY** | compiler exists without automatic policy promotion |
| W6 One-checkout mutation coordination | **CLOSED** | single writer, lease/fence/checkout identity accepted |
| W7 Capability Policy + Secret Broker | **CORE CLOSED; GENERAL WORKER GATE-CLOSED** | safe foundations accepted; full arbitrary-worker isolation not claimed |
| W8 Computer Use | **DEFERRED / GATE-CLOSED** | requires deliberate product/safety opening |
| W9 CAS/artifact identity | **CLOSED** | content/address identity boundary present |
| W10 Trace/replay context | **CLOSED** | trace-context and replay-oriented evidence present |
| W11 MCP 2026 session/reconnect | **SOURCE CLOSED; LIVE ACTIVATION PENDING RESTART at closure** | reconnect/task-context source green; accepted ownership fix needed live activation |
| W12 Reverse relay/device lease | **DEFERRED / GATE-CLOSED** | remote identity/lease/security not opened |
| W13 Detached jobs/restart lifecycle | **CLOSED** | managed process/recovery lifecycle accepted |
| W14 Candidate/shadow routing | **SHADOW-ONLY / NO PROMOTION** | candidate evidence cannot autonomously change production policy |
| W15 External A2A | **DEFERRED / GATE-CLOSED** | no accepted external trust/authority contract |

---

# 4. Current immediate operational boundary

At closure, source engineering and local package content were accepted, but the resident Coding MCP process was still pre-fix relative to the accepted cross-session ownership source.

The required operational sequence, **only when explicitly authorized**, is:

```text
1. restart owning Coding MCP/Electron runtime
2. verify accepted ownership/provenance fix is live
3. prove foreign/unowned direct commands do not inherit another EOCL run/wave
4. obtain one clean artifact provenance proof
5. run zero-billing Execution Hub/OpenCode preflight if RC activation requires it
6. only then make a separate release/commit/push/tag/publish decision
```

Do not mix a new upstream feature transplant into this activation boundary unless the operator intentionally abandons the current RC identity and accepts a new source/package cycle.

---

# 5. Non-negotiable invariants

## I1 — One canonical Coding Tools Runtime authority

Never run two peer runtimes that can independently mutate the same canonical workspace/ledger.

## I2 — EOCL is the mutation/proof control boundary

Run/wave ownership, write lease, proof lineage, acceptance, replan, and terminalization remain canonical.

## I3 — One writer

Multi-client is allowed; multi-writer on the same authoritative checkout is not.

## I4 — Electron/Recovery Host owns trusted lifecycle/root host control

Imported upstream lifecycle code may be used internally but cannot silently become a peer supervisor.

## I5 — Coordinated final acceptance remains explicit

Provider availability, upstream autonomous behavior, or green command output does not imply final local acceptance.

## I6 — `smart-v3` stays compact

Internal intelligence does not automatically create new public tools.

## I7 — Source, focused proof, live activation, package, and release are separate claims

Never collapse them.

## I8 — Durable evidence is not source

`.coding-tools` runtime evidence is preserved according to repository policy but excluded from source identity where defined.

## I9 — Deterministic production authority remains fail-closed where evidence gates require it

Copying an upstream router/model policy does not automatically activate it.

## I10 — Cross-session provenance must be explicit

Unrelated/unowned commands must never borrow another run/wave by global projection.

---

# 6. Forward strategy: upstream-first reuse

## 6.1. Why the strategy changed

The old implementation program correctly avoided broad upstream merges because Coding Web had evolved away from a normal fork.

However, the phrase “port/adapt upstream invariants” can be misread as “study upstream and rewrite locally.” That creates unnecessary local code.

The corrected strategy distinguishes:

- **Git-history synchronization** — often unsafe/expensive;
- **source-level implementation reuse** — often highly valuable.

No merge-base is required to copy a bounded upstream function/module/test/state machine with explicit provenance.

## 6.2. Three ownership zones

### Zone A — Commodity implementation: COPY by default

Examples:

- projection/sparsification;
- validation helpers;
- parsers/serialization;
- chunking/framing;
- content hashing;
- upload/download mechanics;
- timeout/cleanup logic;
- atomic finalization;
- deterministic normalization;
- compatible protocol structs;
- release digest/exact-source verification;
- test fixtures/regressions.

### Zone B — Shared subsystem with different local boundary: COPY + ADAPTER by default

Examples:

- artifact export/resource delivery;
- detached Runner Job ownership;
- Computer Use executor;
- managed OAuth/connect logic;
- task/session protocol adapters;
- remote Runner lifecycle;
- release tooling;
- snapshot/resource handles.

### Zone C — Strategic local core: LOCAL CORE by default

Examples:

- Execution Hub authority;
- Recovery Host architecture;
- ChatWeb/Codex shared-runtime topology;
- EOCL acceptance model;
- single-checkout/single-writer mutation fencing;
- `.coding-tools` causal evidence model;
- cross-session provenance isolation;
- compact `smart-v3` orchestration surface;
- solution economics and promotion gates;
- local operator control plane;
- local routing authority.

Upstream helpers may be reused inside Zone C, but the authority contract remains local.

---

# 7. Mandatory reuse ladder R0-R5

Each material upstream candidate receives one primary classification before mutation.

## R0 — COPY

Use upstream implementation substantially unchanged when behavior, platform, authority, dependencies, and data model are compatible.

Required:

- exact upstream identity;
- upstream/local paths;
- reused tests;
- local focused proof;
- provenance record.

## R1 — COPY + ADAPTER

Preserve upstream core implementation and add a narrow local boundary around authority/storage/identity/lifecycle/transport differences.

Target:

```text
Local authority
   |
thin adapter
   |
upstream-derived core
```

The adapter must not grow into a second implementation.

## R2 — SEMANTIC PORT

Preserve upstream algorithm/state machine/failure semantics/tests but map them into different language/runtime/types where direct copy is impractical.

Document exactly which semantics remain equivalent and which differ.

## R3 — REIMPLEMENT

Local rewrite is last resort.

It requires explicit evidence for all of:

```text
WHY R0 COPY FAILED
WHY R1 COPY+ADAPTER FAILED
WHY R2 SEMANTIC PORT FAILED
WHY LOCAL IMPLEMENTATION IS SMALLER/SAFER/BETTER
WHICH UPSTREAM TESTS/INVARIANTS ARE STILL REUSED
EXPECTED FUTURE SYNC COST
```

Acceptable reasons include inseparable conflicting authority, unacceptable dependency tree, platform incompatibility, stronger security/recovery requirement, proven performance problem, materially different consumer semantics, or legal/operational reuse constraint.

## R4 — DEFER

Use when technically interesting but consumer/prerequisite/product decision is absent.

Examples at closure:

- Computer Use;
- remote device lease;
- managed OAuth without hosted need;
- external A2A.

## R5 — REJECT / NOT APPLICABLE

Use for capabilities that conflict with product architecture or add more system than value.

Examples:

- second peer mutation authority;
- second durable orchestration ledger;
- public-tool explosion;
- speculative distributed mesh;
- irrelevant platform-specific capability;
- duplicate analytics/evidence store.

---

# 8. Upstream intake workflow U0-U10

## U0 — Detect

Trigger sources:

- upstream release;
- security/reliability fix;
- relevant PR/commit family;
- regression in already reused code;
- local problem already solved upstream;
- new concrete consumer.

## U1 — Build bounded evidence packet

Collect:

- repo/PR/commit/release identity;
- changed implementation paths;
- tests;
- migrations/schema;
- failure semantics;
- platform dependencies;
- authority assumptions;
- release notes if relevant.

Do not begin by rereading the entire upstream repository.

## U2 — Map authority boundaries

Required table:

| Boundary | Upstream owner | Coding Web owner | Compatible? |
|---|---|---|---|
| lifecycle | upstream | Recovery Host/Electron | yes/no |
| workspace mutation | upstream | EOCL/Coding Tools | yes/no |
| secret ownership | upstream | local trusted host/Secret Broker | yes/no |
| durable job | upstream | local/Runner mapping | yes/no |
| final acceptance | upstream | ChatWeb/Sol coordinated authority | yes/no |
| artifact identity | upstream | local artifact/run/wave boundary | yes/no |

## U3 — Classify R0-R5

No material upstream implementation wave starts without a reuse classification.

## U4 — Reuse upstream tests first

Priority:

1. exact upstream regression;
2. minimal fixture/type/path adaptation;
3. local-boundary regression;
4. broader local test only when oracle gap remains.

## U5 — Transplant smallest coherent source unit

Prefer a complete useful unit:

- function;
- module;
- parser;
- state machine;
- protocol type;
- migration;
- script;
- bounded subsystem;
- test suite.

Avoid both giant range cherry-pick and manual retyping of many functions.

## U6 — Add thin local adapter

Typical responsibilities:

- map upstream Job to run/wave;
- bind auth principal to local attribution;
- bind artifact handle to local provenance;
- route secret through local Secret Broker;
- gate privileged action through Capability Policy;
- map lifecycle into Recovery Host;
- preserve `smart-v3` public surface.

## U7 — Prove three layers

### A. Upstream behavior

Reused regression demonstrates original behavior.

### B. Local integration

Adapter/authority-boundary behavior passes.

### C. Adjacent invariant

Check at least one credible adjacent risk:

- duplicate authority;
- stale ownership;
- secret leak;
- retry duplication;
- source identity drift;
- tool-count drift;
- recovery conflict.

## U8 — EOCL acceptance

Material local mutation follows normal run/wave/write/proof/acceptance rules.

## U9 — Live/package proof only where applicable

Runtime-affecting:

```text
source accepted -> activate exact accepted source -> live smoke
```

Release-bearing:

```text
source accepted -> package exact source -> package proof -> release decision
```

## U10 — Record provenance

Every accepted material transplant must remain auditable without relying on chat memory.

---

# 9. Upstream provenance contract

For each accepted material upstream adoption, record at least:

```yaml
feature: <name>
upstream_repo: <repo>
upstream_pr: <id or null>
upstream_commit: <exact sha>
upstream_paths:
  - <path>
local_paths:
  - <path>
reuse_mode: COPY | COPY+ADAPTER | SEMANTIC_PORT | REIMPLEMENT
copied_core: true|false
local_adapter:
  - <boundary delta>
upstream_tests_reused:
  - <test>
local_tests_added:
  - <boundary test>
authority_delta: <description>
behavior_delta: <description>
license_notice_checked: true|false
future_sync: <where to compare next>
```

This provenance may live in this master document, a small maintained registry, or a machine-readable file rendered into docs later.

It must **not** become a second execution ledger.

---

# 10. Git strategy for divergent histories

## 10.1. Do not use as default

- broad `git merge upstream/main`;
- large commit-range cherry-pick;
- mass conflict resolution;
- reshaping local directories merely to resemble upstream;
- resetting accepted local authority architecture.

## 10.2. Preferred bounded source transplant

```text
upstream commit/PR
 -> inspect exact changed paths
 -> extract coherent implementation + tests
 -> record source identity
 -> add local adapter only where necessary
 -> focused proof
 -> EOCL acceptance
```

Key rule:

> Git history is a transport/provenance mechanism, not an architectural prerequisite for code reuse.

---

# 11. Capability-by-capability reuse policy

| Capability/family | Current status | Default future reuse mode | Local boundary that must remain |
|---|---|---|---|
| sparse projection | closed | **R0 COPY/sync tests** for real deltas | local result/proof shapes |
| artifact import | closed overlap | **R0/R1** | run/wave provenance |
| artifact export/resource link | consumer-dependent | **R1** | principal/run/wave authorization |
| caller attribution | closed | **R0/R1** for future deltas | attribution must not become authorization |
| Semantic Graph | closed local differentiator | local core + selective R0 helpers | local graph/context contract |
| Context Compiler | closed local differentiator | local core + helper reuse | local evidence/efficacy gate |
| mutation coordinator | closed local differentiator | local core | EOCL/write fence |
| Capability Policy | core closed | local core + primitive reuse | local capability decision |
| Secret Broker | core closed | local core + helper reuse | local trusted secret owner |
| Computer Use Windows | deferred | **R1 when deliberately opened** | capability/approval/trace |
| CAS/content addressing | closed foundation | selective R0 | no second store |
| trace context | closed | R0 standards/helpers | ledger remains canonical |
| MCP task/reconnect | source closed | R0/R1 | EOCL remains authority |
| detached Runner Job | current lifecycle closed; remote-role decision may arise | R1 only if remote Runner remains first-class | local run/wave mapping |
| reverse relay/device lease | deferred | R1/R2 if concrete use case opens | grant/lease/revocation |
| solution shadow | closed shadow | local core | no promotion without representative evidence |
| external A2A | deferred | R4 until consumer | no second agent authority |
| managed OAuth | no current hosted requirement | R1 when needed | local secret/audit authority |
| release engineering | high-value maintenance | R0/R1 | Windows Desktop package/release identity |

---

# 12. Acceptance and promotion gates

## G0 — Consumer/value

There is a real problem, consumer, defect, release need, security need, or measurable benefit.

## G1 — Reuse classification

R0-R5 recorded. R3 requires explicit rejection of R0-R2.

## G2 — Authority

No conflicting authority plane enters the canonical product.

## G3 — Source provenance

Exact upstream/local source identities recorded.

## G4 — Behavioral proof

Upstream regression or equivalent proves the copied/ported invariant.

## G5 — Local-boundary proof

EOCL/auth/lifecycle/secret/artifact/recovery integration proven where relevant.

## G6 — EOCL acceptance

Material mutation reaches accepted/checkpointed state under the proper authority.

## G7 — Live activation

Required only if running-process behavior changes.

## G8 — Package/release

Required only for package/release claims.

## G9 — Future sync

The next engineer can identify origin and intentional divergence without archaeology.

---

# 13. Evaluation and engineering metrics

## 13.1. System-quality metrics

Track where meaningful:

- first-pass acceptance;
- repair/replan count;
- TTAR;
- critical defect/regression escape;
- model-facing bytes/tokens when measured;
- tool hops to causal change;
- semantic hit/fallback/degraded rate;
- Context Compiler precision/miss categories;
- write contention;
- write-lease rejection reason;
- foreign-dirty incidence;
- base/source fingerprint drift rejection;
- candidate attempted-write rejection;
- artifact transfer/dedupe;
- trace correlation completeness;
- secret/policy denial correctness;
- job recovery/lost classification;
- provider/controller cost only when actually measured/reported.

Unknown cost/usage remains unknown, never zero by convenience.

## 13.2. Upstream-reuse metrics

### M1 — Reuse-mode distribution

Count R0/R1/R2/R3/R4/R5. A rising unexplained R3 share is a warning.

### M2 — Upstream Test Reuse Ratio

```text
relevant upstream behavior tests reused
---------------------------------------
relevant upstream behavior tests
```

### M3 — Adapter Delta Ratio

For R1:

```text
local adapter surface
------------------------------
reused core + adapter surface
```

A large adapter suggests the work should be reclassified R2/R3 or reconsidered.

### M4 — Unique Maintenance Surface

Measure new local-only implementation outside strategic differentiators.

### M5 — Upstream Sync Lead Time

Time from identifying a useful upstream fix to locally accepted source.

### M6 — Rework after adoption

Track replans, local adaptation defects, regression escapes.

### M7 — Authority regressions

Hard target:

```text
0 duplicate writers
0 duplicate durable ledgers
0 secret-owner duplication
0 implicit policy promotion
0 cross-session proof contamination
```

### M8 — Public-surface growth

Default target remains eight smart-v3 tools.

---

# 14. Risk controls and rollback

| Risk | Control |
|---|---|
| overengineering | implement concrete consumer/use case only |
| duplicate source of truth | adapter/projection into existing ledger/authority |
| upstream code imports peer authority | authority map before R0/R1 decision |
| adapter becomes rewrite | monitor adapter delta; reclassify |
| semantic/context misses dependency | uncertainty + fallback + representative evaluation |
| concurrent source mutation | one active source lease |
| foreign dirty contamination | pre/post dirty ownership + source/base fingerprint fence |
| reconnect creates duplicate writer | durable owner/lease/reconciliation |
| false-green filtered tests | prove source symbol + exact test identity + actual execution |
| secret exfiltration | opaque handles + scoped injection + deny-by-default |
| retry duplicates side effect | explicit idempotency/unknown/recovering/lost semantics |
| source proof mistaken for live proof | separate activation gate |
| old document overrides new truth | one canonical master + historical sections clearly labeled |
| upstream parity causes pointless reopen | non-retroactivity rule |

Rollback examples:

```text
context compiler          -> existing bounded semantic/text fallback
semantic derived index    -> discard/rebuild; source untouched
mutation coordinator      -> serialized MCP-only writer; never add second writer
privileged worker         -> disabled/fail-closed
OTEL exporter             -> disable exporter; ledger remains canonical
MCP adapter               -> disable negotiation; core Job/EOCL path remains
Computer Use              -> policy disabled
shadow treatment          -> disable enrollment; primary path remains
A2A                       -> keep gateway disabled
```

Rollback never erases durable evidence or pretends side effects did not happen.

---

# 15. Historical ledger — program evolution

This section is intentionally historical. It records the process that produced the current architecture, including intermediate states later superseded.

## 15.1. 2026-08-20 — original active implementation-control program

Historical document retired into this master:

`260820_CODING_WEB_TECHNICAL_EVALUATION_AND_IMPLEMENTATION_PLAN.md`

Historical plan baseline:

```text
Workspace: E:\DEV\Codex-web
Program Git baseline: main @ 66c2d17b68969c3a413b867cc7281f80fbaf4b45
Topology decision: one canonical checkout, one source writer, no Git worktree dependency
Product: Windows Electron Execution Hub + Recovery Host + one Coding Tools MCP Runtime
Contract: smart-v3 / eight public tools
```

The plan converted a proposal into an active implementation-control log and established:

- single-checkout/single-writer topology;
- EOCL/write-lease control;
- separate source/focused/live/package claim levels;
- candidate/shadow no-write rule;
- evidence-based workstream sequencing;
- no broad upstream merge;
- no speculative feature activation.

### Historical S0 — P4 residual closeout

Status then: **ACCEPTED / CHECKPOINTED**.

Recorded run/wave:

```text
RUN  f914183e232d4684aab696e81c1144df
WAVE 5752420f2e44402f885bf9f9b4ec3294
proof fingerprint aec5f237b342c5285efc4b83664964c31c9c3c7e30b54716b6a759b05b306365
```

Focused checks recorded:

```text
test_orchestration_tax.py        3/3 PASS
test_model_extreme_closeout.py   2/2 PASS
```

Material corrections included keeping missing provider usage as unknown/null rather than zero and enforcing deterministic ASCII closeout summary behavior.

### Historical S1 — active control-plan/topology migration

Status then: **ACCEPTED at document/control-contract level**.

Key decisions:

- canonical checkout `E:\DEV\Codex-web`;
- no worktree dependency for this program;
- non-owner lanes read/review/candidate only;
- W6 defined as Single-Checkout Mutation Coordinator;
- W14 shadow defined as candidate-only;
- acceptance required before the next material writer wave.

### Historical S2/W3 — authenticated caller attribution

Status then: **ACCEPTED / CHECKPOINTED**.

```text
BASE      66c2d17b68969c3a413b867cc7281f80fbaf4b45
RUN       405ae4561b174ae9b228fdbdf6a172ec
WAVE      c5ff66f9602e4bfda9982e7d36938bb1
PROOF FP  fba256afea4ff23154eb40fcb91e26f1bee268855ea491033f940debeac03a85
```

Historical changed Rust surfaces:

```text
src/action_audit.rs
src/models.rs
src/action_audit_sessions.rs
src/db/schema.rs
src/db/audit.rs
src/audit_http/routes.rs
src/audit_http/tests.rs
```

Recorded focused proof:

```text
cargo fmt -p webcodex -- --check
  PASS
  proof 52dbf1f3b8a34b069c51d8c6f6209b81

cargo check -p webcodex --lib
  PASS
  proof 406d7725e73b4212982763b9bcea4449

cargo test -p webcodex action_audit --lib
  PASS
  proof 7195b72fb8d84ea89e4f58f54daa470f

cargo test -p webcodex audit_http --lib
  PASS
  proof ab8007c9988a46aaab6dbb65daac39c9

cargo test -p webcodex legacy_action_events_gain_nullable_caller_attribution --lib
  PASS
  proof 8e205c09d55c4493ac21de50c0a26a72
```

Important invariant established:

> attribution records who acted; authorization remains owned by auth/EOCL/policy.

### Historical S2/W1 — false-green sparse oracle incident

This is preserved because it changed the project's proof discipline.

Status at the time: **REPLAN / NOT ACCEPTED**.

```text
BASE      66c2d17b68969c3a413b867cc7281f80fbaf4b45
RUN       e93069ccd8bc4d6bb59daeb14c3cddee
WAVE      84706097ef7f4c81b87bb8b6edb35c89
WORKSPACE FP 49df1bd45be44847a81ecf6f72ac256ef772a2548b2ee066fa371120889e626c
```

Two green command/proof records were rejected because the filtered test command could succeed with zero matching tests:

```text
1e1ed9d7911449d29e30238ad3dcb63b
f2ccc1a24c5c409e9c1db269d0fb980a
```

At that checkpoint the required W1 symbols were absent and no W1 source diff existed.

Permanent lesson created by this incident:

```text
A filtered command exit code is not sufficient proof.
Required source must exist.
Expected exact regression identity must exist.
The exact regression must actually execute.
```

Later accepted source superseded this temporary W1 REPLAN state, but the incident remains an important audit/control precedent.

---

# 16. Historical ledger — 2026-08-21 engineering closure

Historical document retired into this master:

`260821_CODING_WEB_IMPLEMENTATION_CLOSURE.md`

The closure reconciled the 20/8 plan against later implementation and proof.

## 16.1. Closure decision

The closure determined that the 20/8 plan was no longer an open backlog.

Source engineering across S1-S9 was terminal: accepted implementation or explicit gate/defer.

The architecture now included:

1. EOCL run/wave ownership, write lease, proof and acceptance;
2. checkout identity and one-writer mutation discipline;
3. Semantic Graph;
4. Context Compiler;
5. capability and secret boundaries;
6. artifact/CAS identity;
7. trace context;
8. MCP 2026 session/reconnect/task context;
9. managed process lifecycle and Recovery;
10. candidate/shadow no-promotion discipline;
11. explicit fail-closed gates for not-yet-adopted capabilities.

## 16.2. Cross-session provenance defect discovered during RC closure

A genuine multi-session control-plane defect was found:

A direct/unscoped `exec_command` could implicitly inherit a globally projected active run/wave, causing an unrelated conversation/project command to appear inside the current Coding Web orchestration evidence.

Accepted source correction:

- explicit `run_id` and `wave_id` must be paired;
- direct/unscoped omitted ownership remains unowned;
- implicit inheritance is allowed only from actual request-scoped task context;
- legitimate internal EOCL checks propagate their run/wave explicitly;
- explicit mismatch remains fail-closed;
- public schema wording reflects the real ownership contract.

Focused proof after fixture correction:

```text
45/45 PASS
git diff --check PASS
RUN  6ff3fbb8c1524273941378ea4628f2aa
WAVE 875172194c91453e9a82d92c7cd48fa1
```

This incident is a permanent design lesson:

> Context projection is not authority. Ownership must be request-scoped or explicit.

## 16.3. Final current-source MCP proof

```text
RUN    1d034de5c90d4fe8877f1120b8b3a568
WAVE   8f632b5c5e48446b9d5502830bf875a5
SOURCE/WORKTREE FP
48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e
```

Result:

```text
npm run test:mcp
493 passed
3 expected platform-specific skipped
0 failed
189.51 s

proof 04a685bf8f704b0797821d2cc6da03dc

git diff --check PASS
proof 7a2f378b09af4006b9681afa30c8afe0
```

Wave status: **ACCEPTED / CHECKPOINTED**.

## 16.4. P0.3 Recovery proof

```text
35/35 PASS
proof f7b08c6401b24e179e4f68881f20d9f8
RUN   ef55188d86b8409096354a56241b3971
WAVE  0ed226510b8c469683dfe193df7de77a
status ACCEPTED / CHECKPOINTED / CLOSED
```

## 16.5. Production dependency audit

```text
npm run audit:prod PASS
production vulnerabilities: 0
proof fe98a15341524c0bbeaed59a4ab305cf
RUN   4294a5325b23491683f682a4349dfcf4
WAVE  77bade90a0f14742a9f03dcb22c174c5
```

## 16.6. Final local NSIS artifact at closure

```text
Path:
E:\DEV\Codex-web\dist\web-mcp-assistant-setup-0.3.4.exe

Size:
128,832,126 bytes

Local timestamp:
21/08/2026 11:43

SHA-256:
f1300f70f7babbe44b283520392b6a2c3547f8a042987260a5ff496d60d1322f
```

Recorded artifact-content checks:

```text
npm run dist                       PASS  82ae1996e1aa4a7c9b1f07869c5f3955
packaged Recovery smoke            PASS  8f3c42ad87244c7bb3e7076fa77d709e
git diff --check                   PASS  410845d1d38d46c1b8106ff573105808
source-root clean                  PASS  42de68a5d56742da82f12cf77c344178
native SHA-256 command             PASS  6db5846d948f418390915e034ef76170
artifact metadata                  PASS  644b2b4c00ed4b85ae1b7f963d96a274
```

Second short artifact re-proof:

```text
packaged Recovery smoke  d8869474192d479b8c88149621a25750
diff hygiene             75682dd1aa224574a6bcfd4ea9d05381
source-root clean         0e62e45f09b34438addd07dbf3970bfd
SHA-256                   f06bd3393719482aa8019662244334b3
metadata                  c2b0307650644e3ca7c8fcff27cc48e4
```

## 16.7. Why release acceptance was withheld

The package checks themselves passed.

However, the resident MCP process was still running pre-fix ownership code and injected unrelated project commands into closure waves.

Therefore the correct classification was:

```text
artifact content       VERIFIED
accepted source fix    GREEN
resident runtime       STALE relative to accepted source
clean live provenance  NOT YET CLAIMABLE
release acceptance     WITHHELD
```

Affected closure run:

```text
776a18b744aa4dda83ec3a7ca2986d65
```

It was terminalized as **ABORTED / external activation boundary** rather than being left in ambiguous REPLAN.

## 16.8. OpenCode zero-billing preflight

Observed failure:

```text
CONTROL_TIMEOUT: Execution Hub control request timed out.
```

Interpretation:

- control-plane/live-activation failure;
- no actual provider dispatch;
- no provider inference cost;
- not evidence that `opencode-go/deepseek-v4-flash` itself was broken;
- not a source blocker because adapter/routing behavior remained covered by the accepted suite.

Closure classification:

**EXTERNAL LIVE-ACTIVATION / UNVERIFIED.**

## 16.9. Native semantic/LSP status

Observed configuration state:

```text
NATIVE_LSP_BINDING_NOT_CONFIGURED
```

Closure classification:

**P2.1 = BLOCKED_CONFIG / KEEP_TEXT_FALLBACK / NOT SOURCE BLOCKER.**

The Semantic Graph source layer remained valid with deterministic/text fallback.

## 16.10. Intentional gates at closure

These were deliberately kept closed:

- general arbitrary worker execution without complete isolation backend;
- W8 Computer Use;
- W12 remote reverse relay/device lease;
- W15 external A2A;
- W14/P1.3 automatic candidate/shadow promotion;
- P1.2 routing policy promotion without representative paired evidence;
- native LSP until configuration/provider readiness is real.

---

# 17. Historical ledger — upstream strategy evolution

Historical document retired into this master:

`260821_UPSTREAM_FIRST_REUSE_STRATEGY_AND_IMPLEMENTATION_PLAN.md`

The policy was created after recognizing a conceptual gap in the 20/8 plan.

## 17.1. Old interpretation risk

Old planning language emphasized:

```text
upstream invariant
 -> local audit
 -> minimal adapt/port
 -> proof
```

This was correct as a defense against broad merge and conflicting authority, but could lead engineers/models to unnecessarily rewrite commodity upstream implementation.

## 17.2. Corrected policy

The project adopted:

```text
COPY
 -> COPY + ADAPTER
 -> SEMANTIC PORT
 -> REIMPLEMENT only with evidence
 -> DEFER/REJECT
```

This is an engineering-method evolution, not a retroactive reopening of the closed program.

## 17.3. Permanent distinction

Two separate truths must remain visible:

```text
NO BROAD MERGE
```

does **not** imply:

```text
NO SOURCE COPY
```

Coding Web can have divergent Git history and still reuse exact upstream implementation/test surfaces.

## 17.4. Strategic meaning

Local engineering budget should concentrate on true differentiators:

- Execution Hub;
- shared multi-client authority;
- EOCL and deterministic mutation;
- Recovery;
- provenance/evidence;
- operator control;
- model routing/economics;
- safe provider/client integration.

Commodity algorithm/data-plane behavior should be reused when that makes the system smaller and safer.

---

# 18. Current forward backlog after closure

This is not a reopen of S1-S9.

## U-P0 — Finish current live activation boundary first

When explicitly authorized:

```text
restart accepted runtime
 -> prove cross-session fix live
 -> clean provenance proof
 -> zero-billing live preflight if required
 -> release/delivery decision
```

## U-P1 — Sparse upstream drift sync

Only if a real upstream delta matters.

Default mode: R0 copy/test sync.

Do not reopen W1 as unfinished.

## U-P2 — Artifact export/resource-link decision

If ChatWeb needs bounded authenticated retrieval of Office/PDF/image/build artifacts without sending large bytes through model context:

- use R1;
- copy upstream data-plane behavior/tests;
- add local principal/run/wave adapter;
- keep existing public surface.

Otherwise defer.

## U-P3 — Remote Rust Runner role decision

If remote Runner remains first-class, future detached-job reliability deltas should start with R1 upstream reuse.

If Runner is legacy/supporting only, stop chasing full parity.

## U-P4 — Release engineering maintenance

High-value candidates for R0/R1 reuse:

- exact-source identity checks;
- digest verification;
- bundle provenance;
- failed-release recovery;
- package/install smoke;
- release manifest logic.

## U-P5 — Managed OAuth only when hosted/multi-user requirement exists

Do not prebuild it.

If opened, upstream source/tests are the starting point; local work is secret/audit/authority integration.

## U-P6 — Computer Use only with concrete consumer and explicit security opening

When opened:

- start from upstream Windows executor primitives;
- wrap with local Capability Policy, caller attribution, trace, approval, Secret Broker, and task context;
- do not write a new mouse/keyboard/snapshot stack from zero.

---

# 19. Anti-patterns prohibited

## A1 — Concept-only reuse by default

Do not read an upstream PR, understand the idea, and rewrite it locally before attempting source/test reuse.

## A2 — Broad parity development

Do not implement features simply because upstream has them.

## A3 — Architecture overwrite

Do not import peer Server/Runner authority over Execution Hub/EOCL.

## A4 — Test rewrite from memory

Reuse upstream regression when technically possible.

## A5 — Adapter inflation

If a “thin adapter” becomes a second implementation, stop and reclassify.

## A6 — Hidden divergence

Material changes to copied algorithms need an intentional divergence record.

## A7 — Framework before consumer

No generic plugin/adapter/platform system before a concrete reused feature needs it.

## A8 — Copy without license/provenance discipline

Record source identity and preserve applicable obligations.

## A9 — Speculative authority

Never import privileged/auth/mutation/distributed authority merely for parity.

## A10 — Reopen closed phases for aesthetics

Closed phases stay closed unless a real maintenance/reopen trigger exists.

## A11 — Historical document as current backlog

Old statuses may be useful for audit but never override later closure.

## A12 — Proof by exit code alone

A green filtered command is not proof unless the intended test/behavior actually ran.

---

# 20. Historical traceability method

This section defines how future engineers should audit a claim.

## 20.1. Trace a current capability

For a claim such as “W6 mutation coordinator is closed”:

1. find W6 in §3.4;
2. identify the accepted closure source fingerprint in §3.2;
3. find relevant historical closure/run references in §16;
4. inspect current source if the checkout has moved beyond that fingerprint;
5. use EOCL/proof ledger for exact run/wave/proof details when available;
6. never assume old proof covers newer source.

## 20.2. Trace a historical failure

For a claim such as “W1 once had false-green evidence”:

1. go to §15.1 / Historical S2/W1;
2. retrieve RUN `e93069...` and WAVE `847060...` from the durable ledger/report if needed;
3. compare the source fingerprint/baseline with the later accepted closure source;
4. distinguish “failure at that historical checkpoint” from “current capability status.”

## 20.3. Trace an accepted proof

Use this chain:

```text
claim
 -> phase/workstream
 -> source/base fingerprint
 -> RUN
 -> WAVE
 -> proof id(s)
 -> acceptance/checkpoint state
 -> later superseding source if any
```

## 20.4. Trace an upstream-derived implementation in the future

Use:

```text
local capability
 -> reuse mode R0-R5
 -> upstream repo/commit/PR
 -> upstream path/test
 -> local destination
 -> authority delta
 -> local boundary test
 -> EOCL run/wave
 -> accepted source fingerprint
```

## 20.5. Distinguish four time dimensions

Every audit must identify:

- **historical source time** — which source fingerprint existed;
- **proof time** — when exact tests/checks ran;
- **runtime activation time** — which process instance loaded the source;
- **release time** — if/when an artifact was published.

A source commit date alone cannot establish the other three.

---

# 21. Compact proof/run index

This table is not the canonical execution ledger. It is an operator index into historical evidence.

| Subject | Run | Wave | Key proof/result |
|---|---|---|---|
| P4 residual closeout | `f914183e232d4684aab696e81c1144df` | `5752420f2e44402f885bf9f9b4ec3294` | 3/3 + 2/2 PASS; proof fp `aec5f...` |
| W3 caller attribution | `405ae4561b174ae9b228fdbdf6a172ec` | `c5ff66f9602e4bfda9982e7d36938bb1` | Rust fmt/check/action/audit regressions PASS |
| W1 false-green rejected | `e93069ccd8bc4d6bb59daeb14c3cddee` | `84706097ef7f4c81b87bb8b6edb35c89` | rejected despite green filtered commands |
| cross-session ownership fix | `6ff3fbb8c1524273941378ea4628f2aa` | `875172194c91453e9a82d92c7cd48fa1` | 45/45 PASS |
| final MCP regression | `1d034de5c90d4fe8877f1120b8b3a568` | `8f632b5c5e48446b9d5502830bf875a5` | 493 pass / 3 skip / 0 fail |
| P0.3 Recovery | `ef55188d86b8409096354a56241b3971` | `0ed226510b8c469683dfe193df7de77a` | 35/35 PASS |
| production dependency audit | `4294a5325b23491683f682a4349dfcf4` | `77bade90a0f14742a9f03dcb22c174c5` | 0 prod vulnerabilities |
| package provenance affected by stale runtime | `776a18b744aa4dda83ec3a7ca2986d65` | historical affected waves | artifact checks pass; run terminalized ABORTED/external activation boundary |

---

# 22. Decision log

## D-2026-08-20-01 — canonical checkout / single writer

Decision: one canonical checkout; no worktree dependency for this program; one source writer at a time.

Reason: avoid multi-client source contention and keep authority explicit.

Status: retained.

## D-2026-08-20-02 — candidate/shadow no-write

Decision: candidate/shadow lanes cannot direct-apply/commit/promote.

Reason: preserve one-writer and evidence boundary.

Status: retained.

## D-2026-08-20-03 — false-green proof hardening

Decision: exact source/test identity must be established before filtered command success is accepted as behavior proof.

Reason: W1 zero-match incident.

Status: retained permanently.

## D-2026-08-21-01 — engineering program closed

Decision: 20/8 plan no longer used as open backlog; S1-S9 terminal.

Reason: later source and proof substantially completed the architecture.

Status: retained.

## D-2026-08-21-02 — cross-session ownership must be request-scoped/explicit

Decision: unowned direct commands cannot inherit another globally projected run/wave.

Reason: real RC provenance contamination incident.

Status: source accepted; closure required live restart/verification.

## D-2026-08-21-03 — upstream-first reuse

Decision: reuse ladder R0-R5 replaces the implicit “study then rewrite” tendency.

Reason: divergent Git history does not justify duplicate local implementation.

Status: current forward engineering policy.

## D-2026-08-21-04 — one master research/engineering document

Decision: consolidate the 20/8 plan, 21/8 closure, and 21/8 upstream strategy into this master and retire the three old documents.

Reason: prevent future context pollution and contradictory status interpretation while preserving audit history.

Status: effective with creation of this file and retirement of superseded documents.

---

# 23. Definition of Done for future engineering waves

A future material change is complete only when applicable items are satisfied:

1. real consumer/problem is identified;
2. protected architecture invariants are named;
3. upstream candidate is checked where relevant;
4. R0-R5 classification is recorded for upstream-derived work;
5. source provenance is recorded;
6. copied upstream tests are preserved when possible;
7. local adapter is constrained to real boundary differences;
8. no peer authority/store/ledger is accidentally introduced;
9. `smart-v3` remains stable unless explicitly changed;
10. source mutation obeys one-writer EOCL control;
11. deterministic proof actually exercises the intended behavior;
12. source, live, package, release claims remain separate;
13. security/recovery/secret boundaries are not weakened;
14. exact accepted source fingerprint is known;
15. future engineer can identify intentional divergence;
16. current master status is updated if the change alters a listed canonical state.

---

# 24. Maintenance rules for this master document

To prevent the same documentation sprawl from recurring:

## 24.1. Do not create a new dated strategy/closure document for ordinary continuation

Update this file instead.

Create a separate document only when the artifact is inherently separate, for example:

- experiment manifest requiring frozen preregistration;
- release artifact manifest;
- formal security threat model;
- external audit/report that must remain immutable;
- migration specification with its own lifecycle.

## 24.2. Append history rather than rewrite chronology

When current status changes:

- update the current status section;
- add a dated decision/checkpoint entry;
- preserve old run/wave/proof identifiers;
- mark superseded claims explicitly instead of deleting their historical meaning.

## 24.3. Never store private chain-of-thought

Record only:

- objective;
- authority;
- state;
- source identity;
- proof identity;
- decision;
- result;
- remaining risk;
- next action.

## 24.4. Use durable ledger for execution detail

This Markdown is an index and engineering narrative, not a replacement for the append-only EOCL/orchestration ledger.

---

# 25. Final current decision card

```text
CURRENT SOURCE ENGINEERING
  CLOSED / ACCEPTED at recorded closure fingerprint

CURRENT LIVE BOUNDARY AT CLOSURE
  restart + live provenance verification still required

PUBLIC TOOL SURFACE
  smart-v3 = 8

MUTATION AUTHORITY
  one writer through EOCL/write lease

UPSTREAM DEFAULT
  COPY -> COPY+ADAPTER -> SEMANTIC PORT -> REIMPLEMENT -> DEFER/REJECT

CLOSED PHASES
  do not reopen for parity/aesthetics

DEFERRED PRIVILEGED FEATURES
  remain gate-closed until concrete consumer + explicit safety/product decision

EVIDENCE
  source != focused proof != live != package != release

DOCUMENTATION
  this master is the single consolidated research/engineering strategy/history file
```

---

# Appendix A — Retired-document mapping

## A.1. Retired 20/8 technical plan

Old file:

`docs/research/260820_CODING_WEB_TECHNICAL_EVALUATION_AND_IMPLEMENTATION_PLAN.md`

Preserved here:

- original product/topology assumptions;
- S0/S1/S2 historical checkpoints;
- W0-W15 intent;
- W1 false-green incident;
- single-writer decision;
- proof/claim discipline;
- acceptance/risk rules that remain valid;
- old queued states are clearly superseded by §3 current closure.

## A.2. Retired 21/8 implementation closure

Old file:

`docs/research/260821_CODING_WEB_IMPLEMENTATION_CLOSURE.md`

Preserved here:

- final engineering closure classification;
- S1-S9 terminal statuses;
- W0-W15 terminal classifications;
- source/contract fingerprints;
- cross-session defect and accepted fix;
- 493/3/0 full MCP proof;
- Recovery 35/35;
- dependency audit 0 vulnerabilities;
- installer path/size/hash;
- package provenance rejection reason;
- OpenCode preflight classification;
- native LSP classification;
- remaining live activation boundary.

Historical SHA-256 recorded when that closure file was created:

`2d13e54bc48270b93813628d7a3db35e38aab5484b86e2fcacb2956cef67504b`

## A.3. Retired 21/8 upstream-first strategy

Old file:

`docs/research/260821_UPSTREAM_FIRST_REUSE_STRATEGY_AND_IMPLEMENTATION_PLAN.md`

Preserved here:

- doctrine;
- zones A/B/C;
- R0-R5 ladder;
- U0-U10 intake workflow;
- provenance model;
- test-reuse strategy;
- capability matrix;
- metrics;
- anti-patterns;
- non-retroactivity rules;
- forward backlog.

Historical SHA-256 recorded when that strategy file was created:

`587595353e741b6a6ec815c656b3e38ab7cbb0baadcc457bc10cfb2e1be58432`

---

# Appendix B — Checkpoint template

Use for future material additions to this master:

```text
CHECKPOINT: <program / phase / workstream / wave>
TIME: <ISO-8601 + timezone>
STATUS: PLANNED | IN_PROGRESS | REPLAN | ACCEPTING | ACCEPTED | BLOCKED | DEFERRED | SUPERSEDED
BASE: <HEAD + source fingerprint>
RUN/WAVE: <ids if applicable>
UPSTREAM: <repo/pr/commit if applicable>
REUSE MODE: R0 | R1 | R2 | R3 | R4 | R5 | N/A
CHANGED: <paths/surfaces>
PROOF: <exact proof identities and outcomes>
CLAIM: source | focused | live | package | release
DECISION: <what is now true>
HISTORICAL IMPACT: <what prior statement becomes superseded>
RISKS: <remaining material risks>
NEXT: <one critical action>
```

---

# Appendix C — One-page upstream decision card

```text
1. Real consumer/problem?
   NO  -> R4 DEFER
   YES -> continue

2. Compatible code and no authority conflict?
   YES -> R0 COPY
   NO  -> continue

3. Only boundary differs?
   YES -> R1 COPY + ADAPTER
   NO  -> continue

4. Can upstream algorithm/state machine be preserved in local runtime/types?
   YES -> R2 SEMANTIC PORT
   NO  -> continue

5. Is local rewrite demonstrably necessary?
   YES -> R3 REIMPLEMENT + written evidence
   NO  -> R4/R5 DEFER/REJECT

Always:
- reuse upstream tests first
- record exact source identity
- keep EOCL/Recovery/secret authority local
- distinguish historical/current states
- do not reopen closed phases for parity
- separate source/live/package/release claims
```

---

# Appendix D — Terminal summary inherited from closure

| Area | Closure status |
|---|---|
| original 20/8 program | **PRESERVED HERE AS HISTORICAL LEDGER; OLD FILE RETIRED** |
| S1-S9 | **TERMINAL** |
| W0-W7 | **CORE CLOSED**, with general-worker isolation gate |
| W8 | **DEFERRED / GATE-CLOSED** |
| W9-W11 | **SOURCE CLOSED**, W11 resident activation pending restart at closure |
| W12 | **DEFERRED / GATE-CLOSED** |
| W13 | **CLOSED** |
| W14 | **SHADOW-ONLY / NO PROMOTION** |
| W15 | **DEFERRED / GATE-CLOSED** |
| P0.3 | **CLOSED / ACCEPTED** |
| P1.1 source | **CLOSED / ACCEPTED** |
| P1.1 package content | **BUILT / VERIFIED LOCALLY** |
| P1.1 clean live provenance | **PENDING RESTART / NOT RELEASE-ACCEPTED at closure** |
| P1.2 | **EVIDENCE-GATED / KEEP DETERMINISTIC** |
| P1.3 | **NO PROMOTION** |
| P2.1 | **BLOCKED_CONFIG / KEEP FALLBACK** |
| production vulnerabilities | **0 at closure audit** |
| full current-source MCP regression | **493 PASS / 3 EXPECTED SKIP / 0 FAIL at closure fingerprint** |
| final installer | **128,832,126 bytes; SHA-256 `f1300f70f7babbe44b283520392b6a2c3547f8a042987260a5ff496d60d1322f`** |
| release | **NOT PERFORMED / NOT CLAIMED** |

---

# Final statement

> **Coding Web has one consolidated engineering narrative from this point forward. The architecture built through the 20/8 implementation program remains accepted at the recorded source boundary; the 21/8 closure establishes what was actually finished and what remained operational/evidence-gated; the upstream-first policy governs how future deltas are implemented without duplicating solved upstream code. Historical failures, accepted proof, source identities, and policy evolution remain preserved inside this master so future audits can reconstruct both what happened and why, while day-to-day work no longer has to reconcile three competing dated documents.**
