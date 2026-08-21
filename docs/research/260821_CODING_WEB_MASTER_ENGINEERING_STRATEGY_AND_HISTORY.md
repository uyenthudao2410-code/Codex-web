# CODING WEB — MASTER ENGINEERING STRATEGY, GOVERNANCE PLAN & HISTORICAL LEDGER

> **Reconciled edition:** 2026-08-21  
> **Workspace:** `E:\DEV\Codex-web`  
> **Document class:** consolidated research doctrine + governance plan + historical/audit ledger  
> **Operational truth:** current source/runtime/EOCL + maintained product docs, **not this dated research snapshot alone**  
> **Purpose:** preserve one coherent engineering narrative while preventing historical plans, current runtime state, release gates, and future strategy from being confused with each other.

---

# 0. FINAL EXECUTIVE DECISION

Coding Web has reached the point where the main engineering problem is no longer “what additional framework should be built?” The architecture already contains most of the authority, identity, evidence, recovery, routing and execution-control foundations that earlier plans were trying to reach.

The final program decision is therefore:

> **GO for a small, causal truth/traceability hardening program.**  
> **NO-GO for implementing the Case Study G0–G7 as one literal architecture backlog.**  
> **NO-GO for rebuilding Workspace Identity, Evidence Envelope, EOCL, Recovery authority, orchestration state, or a separate upstream-governance system.**

The next engineering value is concentrated in five bounded improvements:

1. **Truth Reconciliation** — reconcile source/proof/live/package/release state and documentation semantics before another broad mutation wave.
2. **Wave Objective Provenance** — bind effective intent/objective to each wave so a REPLAN cannot leave reports carrying stale run semantics.
3. **TruthSnapshot** — compose existing source/runtime/workspace/package/evidence identities into one read-only fail-closed projection.
4. **Operator Truth Console** — show that projection clearly without treating “online” as equivalent to “correct source/package/workspace”.
5. **Executable Engineering Casebook** — convert important historical incidents into deterministic regression oracles.

After those five items:

> **STOP and evaluate.**

Only if real upstream maintenance work exists should the project add a minimal **registry-on-touch** record for the specific capability being reused. Do not build a complete upstream CMDB, delta dashboard, sync daemon, automatic merger, or maintenance engine merely because such a system is architecturally attractive.

The governing engineering doctrine remains:

> **UPSTREAM-FIRST REUSE**  
> **Copy implementation whenever compatible.**  
> **Adapt boundaries, not algorithms.**  
> **Never copy a conflicting authority plane.**  
> **Never reimplement merely because Git histories diverged.**

Short form:

> **Reuse aggressively — integrate conservatively.**  
> **Copy code, not authority.**

---

# 1. DOCUMENT AUTHORITY AND PRECEDENCE

## 1.1. Why this master exists

This file consolidates the engineering lessons, historical closure, upstream-reuse doctrine, decision log, traceability rules, and the bounded hardening plan that emerged from the 2026-08-20/21 implementation program.

It intentionally prevents a return to multiple overlapping research plans that each describe a different point in time as if it were current.

However, **one research master is not the same as one global source of truth for the whole repository**.

A dated research document can preserve history very well while still becoming stale as a live status page. Therefore this file must not override newer source/runtime evidence or maintained operational documents.

## 1.2. Canonical precedence

When two sources disagree, use this order:

1. **Current implementation + authoritative focused/live proof for the exact checkout/process being operated.**
2. **Live runtime contract and EOCL state** for what execution transition, owner, lease, proof or acceptance is legal now.
3. `AGENTS.md` for repository engineering/control rules.
4. `docs/CURRENT_STATE.md` for maintained product/operational truth.
5. `docs/ROADMAP.md` for maintained current priority and planned engineering sequence.
6. Maintained architecture/security/recovery/release/testing documents relevant to the subsystem.
7. **This master document** for doctrine, reconciled strategy, historical context and audit navigation.
8. Durable historical EOCL reports/ledger records when reconstructing past events.
9. Older dated research snapshots, external notes and discussions.

## 1.3. What this document answers

This file is authoritative only for these questions unless a higher-precedence source explicitly supersedes it:

- What engineering principles were learned?
- Why were major architecture decisions made?
- How should future upstream reuse be classified?
- Which historical runs/waves/proofs explain a decision?
- Which broad programs are prohibited as overengineering?
- What bounded hardening sequence has been recommended?
- How should future engineers audit a claim?

It is **not** the sole authority for:

- exact current HEAD;
- exact current process instance;
- exact current package bytes;
- exact current active run/wave;
- exact current release status;
- current priority if `ROADMAP.md` was deliberately updated later.

## 1.4. Non-retroactivity

A new strategy does not retroactively invalidate accepted work.

A previously closed workstream remains closed unless there is a new explicit trigger:

- concrete defect;
- security/reliability correction;
- measurable performance/maintenance benefit;
- concrete product/consumer requirement;
- upstream change materially affecting reused local code;
- explicit operator architecture decision.

**Upstream parity by itself is not a reopen trigger.**

Correct model:

```text
W5 Context Compiler = CLOSED
        |
        +-- real defect -----------------> NEW MAINTENANCE WAVE
        +-- useful upstream delta -------> NEW MAINTENANCE WAVE
        +-- measured product need -------> NEW MAINTENANCE WAVE
```

Incorrect model:

```text
upstream has a newer implementation
        -> reopen W5 as unfinished
```

## 1.5. No third phase ontology

The repository already has historical P/S/W labels. R0–R5 and U0–U10 are **decision/checklist taxonomies**, not runtime orchestration states.

The bounded implementation sequence in this document is only delivery ordering. It must not become another persistent state machine.

Actual execution still uses EOCL RUN/WAVE state:

```text
PREFLIGHT -> READY -> ROUTED -> EXECUTING -> PROVING -> ACCEPTING -> CHECKPOINTED
```

with explicit exceptional states such as `REPLAN`, `BLOCKED`, and `ABORTED`.

---

# 2. PRODUCT AND AUTHORITY INVARIANTS

## 2.1. Product topology

The operated product is a **Windows Electron Execution Hub + Recovery Host + one Coding Tools MCP Runtime**, with substantial WebCodex/Rust/Runner/server code retained as useful foundation/subsystem code rather than treated as the sole product identity.

```text
ChatWeb / ChatGPT
      |
      | MCP over primary tunnel
      v
Recovery Host / Execution Hub authority
      |
      +--> ONE Coding Tools MCP Runtime
      |       |
      |       +--> workspace mutation / commands / proof / EOCL
      |       +--> semantic/context/artifact/runtime helpers
      |
      +--> Electron Execution Control Center
      |
      +--> independent Recovery MCP / Recovery Tunnel
      |
      +--> Codex Desktop thin client/proxy

Secondary provider/model lanes:
  Codex App Server / OpenCode / candidate lanes
  -> bounded candidate, review, read-only, or explicitly authorized execution
  -> never implicit peer authority over the canonical checkout
```

## 2.2. Authority split

| Responsibility | Canonical owner |
|---|---|
| semantic coordination/final go-no-go in coordinated ChatWeb work | ChatWeb/Sol |
| trusted host lifecycle / Recovery supervision | Electron / Recovery Host |
| deterministic workspace mutation and proof | Coding Tools MCP / EOCL |
| source write authority | one active write lease only |
| durable causal execution history | EOCL/orchestration ledger |
| secret-at-rest owner | trusted local host/Electron boundary |
| package/release publication | explicit release authority; never implied by source acceptance |

## 2.3. Public tool contract

`smart-v3` remains intentionally compact at exactly eight public tools unless a future explicit product decision changes it:

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

`restart_runtime` is an action inside `task_control`, not a ninth tool.

## 2.4. Non-negotiable invariants

### I1 — One canonical Runtime authority

Never run two peer Coding Tools runtimes that can independently mutate the same canonical workspace/ledger.

### I2 — One writer

Multiple clients may observe/control through defined contracts; only one active source-write lease may mutate the authoritative checkout.

### I3 — EOCL remains the mutation/proof authority

Run/wave ownership, write lease, proof lineage, replan, acceptance and terminalization remain canonical.

### I4 — Recovery/Electron remains trusted lifecycle authority

Imported upstream lifecycle code may be reused internally but must not silently become a peer supervisor.

### I5 — Source, proof, live, package and release are separate claims

Never collapse:

```text
SOURCE PRESENT
FOCUSED PROOF PASS
EOCL ACCEPTED
LIVE PROCESS ACTIVATED
PACKAGE CONTAINS BYTES
RELEASE PUBLISHED
```

### I6 — Historical evidence is not current source

`.coding-tools/**` is durable evidence according to repository policy, but runtime evidence churn is not source identity.

### I7 — Unknown is not success

Missing package/runtime/provider/usage evidence must remain `UNKNOWN`, not be converted into zero or `MATCHED`.

### I8 — Cross-session ownership is explicit or request-scoped

An unrelated/unowned command must never borrow another run/wave merely because that run is globally projected in UI/task state.

### I9 — Deterministic production policy remains fail-closed where evidence gates require it

Upstream routers, candidate lanes or shadow signals do not activate production policy by existence alone.

### I10 — No duplicate governance subsystem

Do not build a second identity authority, second evidence ledger, second upstream controller, second mutation coordinator, or generic framework that duplicates already accepted local semantics.

---

# 3. CURRENT-TRUTH RECONCILIATION RULE

## 3.1. Historical closure versus current runtime

The 2026-08-21 closure recorded an accepted source boundary around historical HEAD `640ad37e...` and source/worktree fingerprint:

```text
48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e
```

That identity remains valid historical evidence for what was accepted at that checkpoint.

It is **not** automatically current after later commits.

A later live check during the final reconciliation observed the repository at:

```text
branch: main
HEAD: 36ce22300aa4cb628d84d895942aeafd35b6bde6
runtime-reported source dirty: false
runtime version: 0.4.3
smart-v3 tool count: 8
smart-v3 contract SHA:
abd0f63f1653afc356a31d6c2cf23b21ddd01abdaee9d014f4ffa8ad98814a14
semantic localization:
NATIVE_LSP_BINDING_NOT_CONFIGURED
```

This is itself only an observed checkpoint. Future work must re-read the live contract rather than treating this paragraph as perpetual truth.

## 3.2. Important current observation: task projection contamination remains possible

During the same live reconciliation, the current Coding Web workspace/task projection displayed a completed command associated with the separate attendance project.

This observation must be classified carefully:

```text
OBSERVED:
  task/UI projection contained foreign-project command semantics

NOT YET PROVEN BY THAT OBSERVATION ALONE:
  foreign command held Coding Web source write lease
  foreign command inherited Coding Web EOCL ownership
  accepted cross-session exec ownership patch regressed
```

Therefore it is a **truth/projection risk**, not automatic proof of a source-authority regression.

This distinction is a major reason to build TruthSnapshot and improve wave intent/provenance rather than infer authority from UI/task projection.

---

# 4. RECONCILED P0.3 SEMANTICS

A documentation conflict existed because different documents used “P0.3 closed” to mean different acceptance planes.

The correct model is three separate claims:

## P0.3-A — Recovery core/focused engineering

```text
STATUS: CLOSED / ACCEPTED
RUN:  ef55188d86b8409096354a56241b3971
WAVE: 0ed226510b8c469683dfe193df7de77a
FOCUSED RESULT: 35/35 PASS
PROOF: f7b08c6401b24e179e4f68881f20d9f8
```

Meaning:

- the focused Recovery engineering behavior represented by that accepted source/proof was closed;
- this is a valid historical source/proof claim.

## P0.3-B — Production Recovery fault matrix

```text
STATUS: PENDING / RELEASE-HARDENING WORKSTREAM
SCOPE: controlled production-like F1–F9 fault matrix
```

This is the work described in `docs/PRODUCTION_CLOSURE_ROLLOUT.md` and is not automatically satisfied by the 35/35 focused Recovery proof.

Examples include controlled ownership/fault cases around:

- UI/Electron exit/restart;
- Recovery Host exit;
- Recovery MCP exit;
- Recovery Tunnel exit;
- primary MCP/Tunnel exit;
- stale ownership/lock;
- live-but-unhealthy owner;
- repeated Recovery Host crash/backoff.

## P0.3-C — True reboot/logon persistence

```text
STATUS: EXTERNAL / UNVERIFIED unless independently executed and observed
```

Current-session Scheduled Task proof cannot be upgraded into true reboot/logon proof by inference.

## 4.1. Permanent reporting rule

Never again write simply:

```text
P0.3 = CLOSED
```

without naming the claim plane.

Required form:

```text
P0.3 core/focused = CLOSED
P0.3 production fault matrix = PENDING or CLOSED with exact evidence
reboot/logon persistence = VERIFIED or EXTERNAL/UNVERIFIED
```

---

# 5. ENGINEERING PROGRAM CLOSURE

The broad S1–S9 architecture/control program is not to be reopened for parity or aesthetic completeness.

Historical accepted/deferred classification:

| Area | Classification |
|---|---|
| S1–S9 broad architecture/control program | TERMINAL for accepted baseline |
| W0–W7 core foundations | CLOSED, with privileged-worker isolation gate where applicable |
| W8 Computer Use | DEFERRED / GATE-CLOSED |
| W9–W11 source foundations | CLOSED at historical accepted source boundary; live claims remain source-specific |
| W12 reverse relay/device lease | DEFERRED / GATE-CLOSED |
| W13 process/recovery lifecycle | CLOSED at accepted source boundary |
| W14 solution shadow | SHADOW-ONLY / NO PROMOTION |
| W15 external A2A | DEFERRED / GATE-CLOSED |
| automatic non-deterministic routing | OFF unless representative evidence clears the maintained gate |
| native LSP | `NATIVE_LSP_BINDING_NOT_CONFIGURED`; text fallback retained |

“Closed” here means either:

- accepted implementation/proof for the recorded source boundary; or
- accepted fail-closed/defer decision because prerequisites/consumer were absent.

It does **not** imply:

- all later source has been re-proven by old proofs;
- package/release is complete;
- deferred privileged capabilities are active;
- production fault matrix is complete;
- automatic routing promotion is allowed.

---

# 6. FINAL TECHNICAL DIAGNOSIS

## 6.1. What the project already has

The case-study concepts must be evaluated against existing implementation, not treated as greenfield requirements.

| Proposed concept | Existing reality | Final decision |
|---|---|---|
| Workspace Identity Capsule | canonical root, branch/HEAD, source/worktree fingerprints, run/wave, session/client/device ownership checks already exist | **Do not build a second identity subsystem; compose projection only** |
| Evidence Envelope | run/wave/proof/checkpoint, provenance, artifact lineage, source/worktree identity already exist | **Do not build a second evidence framework; patch missing fields only** |
| Runtime Identity Envelope | process/server instance, runtime/code/loaded-behavior/tool-contract identity already exist | **Reuse existing fields** |
| Writer/authority ownership | EOCL + write lease/fence + control/acceptance roles already exist | **Do not create another authority framework** |
| Truth Chain | source/runtime/workspace evidence largely exists; package projection remains fragmented | **Build read-only TruthSnapshot only** |
| Upstream Registry | no small maintained machine-readable registry yet | **registry-on-touch only** |
| Truth Console | UI exists but “online” and provenance truth are not sufficiently separated | **GO as thin projection UI** |
| Executable Casebook | many individual regressions exist but incidents are not centrally organized as a deterministic casebook | **GO, without generic replay framework** |
| Evidence economics | P4/P5/P7/solution-shadow infrastructure already exists | **Continue existing program; do not create G6** |

## 6.2. The real remaining gaps

The final diagnosis reduces the open engineering problem to:

1. **documentation/current-truth reconciliation**;
2. **effective wave intent provenance**;
3. **unified read-only truth projection**;
4. **operator-visible truth separation**;
5. **deterministic historical incident regression**;
6. **upstream provenance only when real upstream work is touched**.

This is a much smaller problem than rebuilding governance.

---

# 7. DEFECT 1 — WAVE OBJECTIVE PROVENANCE

## 7.1. Proven historical incident

A real traceability defect was identified around:

```text
RUN:
6ff3fbb8c1524273941378ea4628f2aa

FINAL WAVE:
875172194c91453e9a82d92c7cd48fa1
```

The accepted wave materially addressed the **cross-session EOCL provenance leak**, but generated reporting still carried stale run-objective semantics associated with building/verifying the NSIS release candidate.

Conceptually:

```text
RUN initial objective
    Build NSIS
        |
      REPLAN
        v
WAVE effective objective
    Fix cross-session provenance leak
        |
        v
Generated report
    still inherits old run objective
```

This creates a real audit defect even if source mutation and proof are technically correct.

## 7.2. Why it matters

Stale objective identity can corrupt or weaken:

- human forensic interpretation;
- generated run/wave reports;
- solution-economics task classification;
- rework/economics analysis;
- historical retrieval;
- future AI context reconstruction;
- causal linkage between intent, mutation, proof and acceptance.

## 7.3. Minimal implementation target

Do **not** build `EvidenceEnvelopeService`.

The minimal data model should conceptually support:

```text
run.initial_objective

wave.effective_objective
wave.objective_revision
wave.objective_sha256
wave.objective_source
wave.objective_changed_from_previous
```

The exact field names may be adapted to current schema conventions, but the semantics must remain.

At PREPARE or explicit REPLAN:

```text
current task intent
      |
      v
bind/snapshot effective objective
      |
      v
wave objective identity
      |
      +--> proof/checkpoint
      +--> generated report
      +--> economics/analytics classification
```

## 7.4. Required report semantics

A report should make the distinction explicit:

```text
Run initial objective: <...>
Wave effective objective: <...>
Objective changed from prior wave: yes/no
Objective revision/hash: <...>
```

## 7.5. Required regression

Deterministic regression:

```text
Wave 1:
  objective = Build installer

REPLAN with a materially different goal

Wave 2:
  objective = Fix provenance defect

ACCEPT Wave 2

EXPECTED:
  Wave 2 report says Fix provenance defect
  Run initial objective remains Build installer as history
  report does not mislabel Wave 2 as Build installer
```

## 7.6. Acceptance criteria

- no stale objective after explicit REPLAN;
- run history is preserved;
- wave effective intent is separately auditable;
- objective hash/revision is deterministic/content-bounded according to current ledger policy;
- no new public tool;
- no new ledger;
- no new authority plane;
- existing run/wave acceptance semantics remain intact.

---

# 8. TRUTHSNAPSHOT — PROJECTION, NOT SYSTEM

## 8.1. Goal

Build one internal read-only object that answers:

1. What source is on disk?
2. What bytes/revision does the running process attest to?
3. Which workspace/device is that process serving?
4. Which package, if any, contains the running/accepted bytes?
5. Which run/wave/proof/acceptance supports the claim?

## 8.2. Proposed conceptual contract

```text
TruthSnapshot
  observed_at

  source:
    canonical_root
    branch
    head
    worktree_fingerprint
    disk_component_revision
    dirty

  runtime:
    process_instance_id
    server_instance_id
    running_code_revision
    loaded_behavior_fingerprint
    runtime_version
    tool_profile
    tool_count
    tool_contract_sha256

  workspace:
    configured_root
    runtime_root
    workspace_identity
    device_id
    ownership_status

  package:
    runtime_mode
    module_root
    package_manifest_sha256
    packaged_resource_revision

  evidence:
    run_id
    wave_id
    proof_fingerprint
    acceptance_state

  matches:
    source_to_runtime
    runtime_to_workspace
    package_to_runtime
    evidence_to_source
```

## 8.3. Allowed match states

Every derived match is one of:

```text
MATCHED
MISMATCHED
UNKNOWN
NOT_APPLICABLE
```

No implicit “probably matched”.

## 8.4. Source → Runtime rule

Do not compare Git HEAD alone.

Use available evidence such as:

- running code revision;
- current disk component revision;
- loaded behavior attestation;
- runtime/MCP health revision;
- worktree/source fingerprint where supported.

Same HEAD with changed worktree bytes is not sufficient to claim exact runtime identity.

## 8.5. Runtime → Workspace rule

Check available evidence such as:

- canonical configured path;
- runtime-reported workspace root;
- workspace identity/fingerprint;
- device ownership;
- active authority projection.

A running MCP endpoint is not proof that it serves the intended workspace.

## 8.6. Package → Runtime rule

Only claim `MATCHED` when package evidence actually exists.

Typical requirements:

- runtime mode is packaged where package comparison applies;
- module/resource root belongs to packaged resources;
- package/resource manifest or exact-source projection agrees with runtime revision;
- process instance belongs to the relevant activation.

In development mode, package truth may legitimately be:

```text
NOT_APPLICABLE
```

or:

```text
UNKNOWN
```

depending on the question being asked.

Do not generate a fake package identity from Git HEAD.

## 8.7. Evidence → Source rule

A proof/checkpoint must remain bound to the exact relevant source/worktree/contract fingerprint.

Old proof is historical evidence, not proof for newer source.

## 8.8. Non-goals

TruthSnapshot must not introduce:

- a database;
- another source of truth;
- another public MCP tool;
- mutation controls;
- package fabrication;
- background sync engine;
- new authority ownership.

It is a **composite projection over existing truth sources**.

---

# 9. OPERATOR TRUTH CONSOLE

## 9.1. Goal

The operator should be able to answer four questions from one compact view:

1. Which source is current?
2. Which code is actually running?
3. Which workspace is that runtime serving?
4. Which package/release identity, if any, contains those bytes?

## 9.2. UX principle

Separate **transport readiness** from **provenance truth**.

Bad inference:

```text
MCP ONLINE + TUNNEL READY
        => correct code/workspace/package
```

Correct representation:

```text
Transport            ONLINE
Runtime source       MATCHED / MISMATCHED / UNKNOWN
Workspace            MATCHED / MISMATCHED / UNKNOWN
Package              MATCHED / MISMATCHED / UNKNOWN / N/A
Tool contract        SMART-V3 · 8
Evidence             run/wave/proof summary
Process              short process/server identities
```

## 9.3. UI architecture

The renderer must not independently re-derive truth from scattered fields.

```text
Existing authoritative sources
        |
        v
TruthSnapshot service/projection
        |
        v
Execution Control Center card
```

The UI is a consumer, not an authority.

## 9.4. Required focused tests

At minimum:

1. disk/source updated while resident process still reports old revision -> `MISMATCHED`;
2. runtime serves another workspace -> `MISMATCHED`;
3. missing evidence -> `UNKNOWN`, never green;
4. packaged resource root/revision mismatch -> `MISMATCHED` or fail-closed;
5. development mode does not invent package truth;
6. controlled activation changes process/server identity where expected;
7. tool contract not equal to expected `smart-v3 = 8` -> contract mismatch;
8. transport online while provenance unknown -> UI shows both states separately.

---

# 10. EXECUTABLE ENGINEERING CASEBOOK

## 10.1. Goal

Turn historical incidents into executable engineering memory.

Do not build a generic replay engine. Use existing Node/Python/Rust test infrastructure.

Each case should capture:

- incident ID;
- historical failure mode;
- protected invariant;
- deterministic setup;
- expected status/error;
- current regression test path;
- relevant historical run/wave/proof reference;
- no model/provider requirement.

## 10.2. Minimum case set

| Case | Historical failure mode | Required invariant |
|---|---|---|
| C01 | runtime serves wrong workspace | fail-closed / mismatch visible |
| C02 | disk source new, process old | source/runtime mismatch visible; no false activation claim |
| C03 | development launch points at another checkout | refuse/reconcile; no silent reuse |
| C04 | packaged resources stale versus source | package/runtime/source mismatch detected |
| C05 | evidence cohort missing pair/oracle/environment | no promotion |
| C06 | write lease/base/source/worktree drift | no mutation; explicit replan/failure |
| C07 | structural precondition changes after REPLAN | new wave/effective intent; no blind retry |
| C08 | sparse persisted Recovery state | safe normalization or explicit fail-closed behavior |
| C09 | smart-v3 public tool count drifts from 8 unexpectedly | acceptance fails |
| C10 | UI says online but provenance truth unknown | online remains separate from accepted/current |
| C11 | filtered test exits green with zero intended test | proof rejected |
| C12 | unowned cross-session command attempts to inherit projected run/wave | remains unowned / fails mismatch |
| C13 | wave objective changes but report keeps run objective | regression fails until effective wave objective is correct |

## 10.3. Acceptance criteria

- completely deterministic;
- no API key;
- no model inference;
- no provider billing;
- no new generic test framework unless an existing framework cannot express a proven case;
- each major historical incident has an executable oracle or an explicit documented reason why it cannot yet be reproduced safely.

---

# 11. UPSTREAM-FIRST REUSE TAXONOMY

Use only one canonical machine/policy taxonomy:

## R0 — COPY

Copy upstream implementation substantially unchanged when behavior, platform, authority and dependencies are compatible.

Required:

- exact upstream identity;
- upstream/local paths;
- applicable license/notice review;
- reused upstream tests;
- local focused proof.

## R1 — COPY + ADAPTER

Preserve upstream core implementation and add a thin local boundary for authority/storage/identity/lifecycle/transport differences.

Target shape:

```text
Local authority
    |
thin adapter
    |
upstream-derived core
```

## R2 — SEMANTIC PORT

Preserve upstream algorithm/state machine/failure semantics/tests while mapping to different runtime/language/types.

## R3 — REIMPLEMENT

Last resort.

Requires written evidence:

```text
WHY R0 FAILED
WHY R1 FAILED
WHY R2 FAILED
WHY LOCAL REIMPLEMENTATION IS SAFER/SMALLER/BETTER
WHICH UPSTREAM INVARIANTS/TESTS ARE STILL REUSED
EXPECTED FUTURE SYNC COST
```

## R4 — DEFER

Useful concept, but consumer/prerequisite/product decision is absent.

## R5 — REJECT / NOT APPLICABLE

Conflicts with current architecture or adds more maintenance surface than value.

`ADOPT / ADAPT / FORK / BUILD` from older prose may be retained only as human explanatory words. They must not become a second schema taxonomy.

---

# 12. UPSTREAM INTAKE CHECKLIST U0–U10

These are checklist steps, not orchestration states.

## U0 — Detect real trigger

Trigger only on:

- useful upstream release/fix;
- security/reliability delta;
- local bug already solved upstream;
- concrete product consumer;
- upstream change affecting already reused local implementation.

## U1 — Build bounded evidence packet

Collect exact repo/commit/PR, paths, tests, migrations, dependencies, authority assumptions and failure semantics.

Do not read an entire upstream repository by default.

## U2 — Map authority boundary

Identify what upstream assumes versus what Coding Web owns.

## U3 — Choose R0–R5

No material upstream adoption starts without classification.

## U4 — Reuse upstream tests first

Exact upstream regression -> minimal fixture adaptation -> local boundary test -> broader tests only when needed.

## U5 — Transplant smallest coherent source unit

Function/module/parser/state machine/protocol type/migration/script/bounded subsystem, not giant history synchronization.

## U6 — Add thin local adapter only where necessary

Typical boundaries:

- run/wave ownership;
- principal attribution;
- artifact provenance;
- secret resolution;
- Recovery lifecycle;
- Capability Policy;
- existing smart-v3 surface.

## U7 — Prove three layers

1. upstream behavior;
2. local integration;
3. one credible adjacent invariant.

## U8 — EOCL acceptance

Normal local mutation rules remain authoritative.

## U9 — Live/package proof only when the changed behavior requires those claims

## U10 — Record provenance

Enough for a future engineer to sync without archaeology.

---

# 13. REGISTRY-ON-TOUCH, NOT FULL INVENTORY

## 13.1. Decision

Do **not** immediately catalog every capability/file in the repository.

A full inventory would quickly become a mini-CMDB with:

- schema burden;
- stale ownership entries;
- review obligations;
- context overhead;
- false completeness.

Instead:

> **Create or extend an upstream capability registry only when a capability is actually being reused, synchronized, ported, rejected, or materially maintained against upstream.**

## 13.2. Minimal record

A future machine-readable record may use a compact JSON file such as:

`config/upstream-capabilities.json`

but it should be created only when the first real consumer exists.

Suggested fields:

```json
{
  "capability_id": "context-compiler",
  "status": "active",
  "reuse_mode": "R2",
  "authority_owner": "coding-tools-mcp",
  "upstream": {
    "repository": "owner/repository",
    "revision": "exact-commit-or-tag",
    "license": "..."
  },
  "local_paths": ["..."],
  "protected_tests": ["..."],
  "semantic_delta": "...",
  "last_reviewed_at": "YYYY-MM-DD"
}
```

## 13.3. Minimum validator semantics when registry exists

- unique capability ID;
- reuse mode only R0–R5;
- R0/R1/R2 require exact upstream revision and license metadata where legally relevant;
- R3 requires rationale;
- active local/test paths must exist or be explicitly planned;
- conflicting authority ownership is rejected;
- secrets/tokens/credential locators are forbidden;
- no public tool or runtime process is created merely to service the registry.

## 13.4. Context projection rule

Do not put the whole registry in every model prompt.

Only project a compact record when task paths intersect a registered capability.

Example:

```text
upstream_governance:
  capability: context-compiler
  reuse_mode: R2
  authority_owner: coding-tools-mcp
  upstream_revision: <short-ref>
  protected_tests:
    - test_context_compiler.py
```

Unrelated tasks receive no registry context.

---

# 14. FINAL IMPLEMENTATION SEQUENCE

The following is a **delivery sequence**, not a new runtime phase system.

Each material implementation item gets its own normal EOCL RUN/WAVE and acceptance.

## Sequence 1 — Truth Reconciliation

### Nature

Docs/evidence/read-only first.

### Objective

Create one reconciled truth matrix for important claims:

```text
CAPABILITY / CLAIM     SOURCE   PROOF   LIVE   PACKAGE   RELEASE
```

Each cell must be an evidence-backed state, not an assumption.

### Mandatory topics

- current source HEAD/fingerprint at execution time;
- current runtime revision/process identity;
- current workspace identity;
- P0.3-A focused Recovery closure;
- P0.3-B production fault matrix;
- P0.3-C reboot/logon persistence;
- cross-session ownership fix source/live status;
- package/release status if relevant;
- current `CURRENT_STATE.md` / `ROADMAP.md` / rollout semantic consistency;
- active writer/lease/quiescence before source mutation.

### Exit gate

- no two maintained documents use the same label to mean contradictory claim planes;
- exact disk/runtime distinction is explicit;
- unknown package/release state stays unknown;
- the next mutation wave has a clear source/delivery boundary;
- no stale active writer is silently inherited.

## Sequence 2 — Wave Objective Provenance

### Nature

First recommended source-code change.

### Objective

Bind effective objective identity to every wave and generated report.

### Exit gate

- REPLAN with changed goal produces a new effective wave objective;
- run initial objective remains preserved as history;
- proof/report/economics can reference the effective wave objective;
- regression based on `6ff3.../875172...` behavior passes;
- no new authority or public tool.

## Sequence 3 — TruthSnapshot

### Nature

Read-only backend projection.

### Exit gate

- source/runtime/workspace/package/evidence truth is composable;
- every comparison is `MATCHED/MISMATCHED/UNKNOWN/NOT_APPLICABLE`;
- no fake green state from missing evidence;
- no DB/new authority/new ledger/public tool.

## Sequence 4 — Operator Truth Console

### Nature

UI projection only.

### Exit gate

Operator can distinguish:

- service online;
- runtime/source matched;
- workspace matched;
- package truth;
- smart-v3 contract;
- process/server identity;
- run/wave/proof state.

UI derives from TruthSnapshot, not ad-hoc renderer heuristics.

## Sequence 5 — Executable Engineering Casebook

### Nature

Regression/test organization.

### Exit gate

- high-value historical incidents are represented by deterministic tests or explicit safe-defer reasons;
- no generic replay engine;
- no provider/model dependency;
- no separate casebook authority store.

## STOP / EVALUATE GATE

After Sequence 5:

```text
STOP
  |
  +--> Do truth/provenance incidents materially decrease?
  +--> Is operator diagnosis faster?
  +--> Are historical regressions easier to catch?
  +--> Is context/tool overhead stable or lower?
  +--> Has a real upstream maintenance event occurred?
```

Only then decide whether a further automation/delta capability is justified.

---

# 15. CASE-STUDY G0–G7 RECONCILIATION

The old Case Study G0–G7 remains valuable as analysis, not as a literal backlog.

| Case Study concept | Final disposition |
|---|---|
| G0 Inventory/Baseline | absorb into **Truth Reconciliation**; no perpetual full inventory program |
| G1 Identity Envelope | existing backend is sufficient; projection only |
| G2 Truth Chain | implement **TruthSnapshot**, not a Truth subsystem |
| G3 Upstream Intake | use R0–R5 + registry-on-touch only when needed |
| G4 Truth Console / Delta Map | **Truth Console GO**; full Delta Map DEFER |
| G5 Executable Casebook | **GO**, use existing test frameworks |
| G6 Evidence Economics | continue existing P4/P5/P7/solution-shadow; no duplicate program |
| G7 Maintenance Automation | DEFER until repeated real upstream events justify it |

Therefore:

> **NO-GO for “implement G0 through G7”.**  
> **GO for the bounded delta sequence in §14.**

---

# 16. EXPLICIT NON-GOALS / ANTI-OVERENGINEERING BOUNDARY

Do not implement in this program:

- upstream database;
- upstream sync daemon;
- automatic upstream merge/cherry-pick engine;
- second orchestration ledger;
- second workspace identity authority;
- generic Evidence Envelope framework;
- generic Truth System/database;
- new runtime states for R0–R5/U0–U10;
- ninth public MCP tool;
- generic replay/benchmark engine;
- full upstream capability inventory;
- automatic registry context injection into every task;
- automatic non-deterministic routing;
- automatic Context Compiler injection;
- automatic shadow promotion;
- Computer Use without concrete consumer + policy;
- remote device lease without full grant/expiry/reconnect/revocation contract;
- external A2A without a concrete consumer;
- native semantic/LSP activation when binding remains unconfigured;
- package `MATCHED` claims without package evidence;
- reopening P0–P3/S1–S9 simply because a new idea or upstream feature appears.

---

# 17. ACCEPTANCE POLICY FOR FUTURE WAVES

A future material change is complete only when applicable items are satisfied:

1. real defect/consumer/value exists;
2. protected invariants are named;
3. exact current source/base/workspace is known;
4. upstream candidate is checked when relevant;
5. R0–R5 classification exists for upstream-derived work;
6. source/provenance identity is recorded;
7. upstream tests are reused where technically possible;
8. local adapter is limited to actual boundary differences;
9. no peer authority/store/ledger is introduced accidentally;
10. smart-v3 remains stable unless explicitly changed;
11. one-writer EOCL control is respected;
12. deterministic proof actually executes the intended behavior;
13. source/live/package/release claims remain separate;
14. exact accepted fingerprint is known;
15. one credible adjacent risk is checked;
16. generated report carries correct effective wave objective;
17. maintained current-state/roadmap docs are updated if the accepted change alters operational truth or priority;
18. historical evidence remains traceable rather than overwritten.

---

# 18. HISTORICAL ENGINEERING LEDGER

This section is intentionally historical. It preserves the chronology needed for future forensic work and must not be read as an active backlog.

## 18.1. 2026-08-20 program foundation

Historical program baseline:

```text
Workspace: E:\DEV\Codex-web
Program baseline HEAD:
66c2d17b68969c3a413b867cc7281f80fbaf4b45

Core decisions:
- one canonical checkout
- one source writer
- EOCL/write-lease control
- source/proof/live/package claims separate
- candidate/shadow no-write
- no broad upstream merge
- evidence-based acceptance
```

### P4 residual closeout

```text
RUN  f914183e232d4684aab696e81c1144df
WAVE 5752420f2e44402f885bf9f9b4ec3294
proof fingerprint:
aec5f237b342c5285efc4b83664964c31c9c3c7e30b54716b6a759b05b306365
```

Historical focused checks included 3/3 and 2/2 PASS for the recorded closeout tests.

### W3 caller attribution

```text
RUN  405ae4561b174ae9b228fdbdf6a172ec
WAVE c5ff66f9602e4bfda9982e7d36938bb1
PROOF FP:
fba256afea4ff23154eb40fcb91e26f1bee268855ea491033f940debeac03a85
```

Permanent invariant:

> Attribution records who acted; authorization remains owned by auth/EOCL/policy.

### W1 false-green incident

```text
RUN  e93069ccd8bc4d6bb59daeb14c3cddee
WAVE 84706097ef7f4c81b87bb8b6edb35c89
WORKSPACE FP:
49df1bd45be44847a81ecf6f72ac256ef772a2548b2ee066fa371120889e626c
```

Two green filtered commands were rejected because zero matching tests could still return success.

Permanent rule:

```text
required source symbol must exist
+ exact intended test identity must exist
+ exact intended regression must execute
+ exit code alone is insufficient
```

This historical REPLAN was later superseded by accepted implementation, but the incident remains a permanent proof-control precedent.

## 18.2. 2026-08-21 broad engineering closure

Historical closure HEAD:

```text
640ad37e3e571a0a56af376e9d3bda2b89bf0669
```

Historical accepted source/worktree fingerprint:

```text
48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e
```

Historical smart-v3 contract SHA recorded around closure:

```text
abd0f63f1653afc356a31d6c2cf23b21ddd01abdaee9d014f4ffa8ad98814a14
```

### Cross-session ownership/provenance defect

Problem:

An unscoped direct command could inherit a globally projected active run/wave instead of remaining unowned unless actual request-scoped ownership existed.

Accepted source correction established:

- explicit `run_id` + `wave_id` must be paired;
- unscoped omitted ownership remains unowned;
- implicit inheritance only from real request-scoped task context;
- internal EOCL checks propagate legitimate ownership explicitly;
- mismatch fails closed.

Focused proof:

```text
45/45 PASS
RUN  6ff3fbb8c1524273941378ea4628f2aa
WAVE 875172194c91453e9a82d92c7cd48fa1
```

This same historical run later became the evidence source for the **wave-objective provenance defect** described in §7: ownership behavior could be corrected while report intent remained stale.

### Final MCP regression at closure fingerprint

```text
RUN    1d034de5c90d4fe8877f1120b8b3a568
WAVE   8f632b5c5e48446b9d5502830bf875a5
SOURCE FP:
48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e

npm run test:mcp
493 passed
3 expected platform-specific skipped
0 failed

proof:
04a685bf8f704b0797821d2cc6da03dc
```

### P0.3 Recovery focused proof

```text
RUN  ef55188d86b8409096354a56241b3971
WAVE 0ed226510b8c469683dfe193df7de77a
35/35 PASS
proof f7b08c6401b24e179e4f68881f20d9f8
```

Historical interpretation is now narrowed by §4:

- core/focused Recovery closed;
- production F1–F9 fault matrix is a separate claim;
- reboot/logon persistence is another separate claim.

### Production dependency audit

```text
RUN  4294a5325b23491683f682a4349dfcf4
WAVE 77bade90a0f14742a9f03dcb22c174c5
production vulnerabilities: 0
proof fe98a15341524c0bbeaed59a4ab305cf
```

### Historical NSIS artifact

```text
E:\DEV\Codex-web\dist\web-mcp-assistant-setup-0.3.4.exe
size: 128,832,126 bytes
SHA-256:
f1300f70f7babbe44b283520392b6a2c3547f8a042987260a5ff496d60d1322f
```

That artifact identity is historical. Later source changes automatically make it stale for claims about newer source.

## 18.3. S6–S9 terminal decisions

Historical closure evidence established terminal architecture/control decisions for:

- S6/W7 capability policy + Secret Broker foundation, with general privileged worker still fail-closed because a fully verified isolation backend was absent;
- S7 trace/runtime/process foundations;
- W8 Computer Use deferred;
- W12 remote device lease deferred;
- W14 shadow-only/no promotion;
- W15 external A2A deferred.

These are accepted closed/defer decisions, not invitations to create placeholder implementations.

## 18.4. Upstream strategy evolution

Old risk:

```text
upstream invariant
 -> local audit
 -> local adapt/port
```

could be interpreted as “study upstream then rewrite locally”.

Corrected policy:

```text
R0 COPY
 -> R1 COPY + ADAPTER
 -> R2 SEMANTIC PORT
 -> R3 REIMPLEMENT only with evidence
 -> R4 DEFER
 -> R5 REJECT
```

Permanent distinction:

```text
NO BROAD GIT MERGE
```

does not imply:

```text
NO SOURCE-LEVEL CODE/TEST REUSE
```

---

# 19. COMPACT RUN/WAVE/PROOF INDEX

This index is a navigation aid, not a replacement for the durable EOCL ledger.

| Subject | Run | Wave | Key evidence/result |
|---|---|---|---|
| P4 residual closeout | `f914183e232d4684aab696e81c1144df` | `5752420f2e44402f885bf9f9b4ec3294` | 3/3 + 2/2 historical focused PASS; proof fp `aec5f...` |
| W3 caller attribution | `405ae4561b174ae9b228fdbdf6a172ec` | `c5ff66f9602e4bfda9982e7d36938bb1` | Rust attribution regressions PASS |
| W1 false-green rejected | `e93069ccd8bc4d6bb59daeb14c3cddee` | `84706097ef7f4c81b87bb8b6edb35c89` | green filtered commands rejected because intended test/source was absent |
| cross-session ownership fix | `6ff3fbb8c1524273941378ea4628f2aa` | `875172194c91453e9a82d92c7cd48fa1` | 45/45 PASS; also exposes stale objective-report semantics |
| final MCP regression at closure | `1d034de5c90d4fe8877f1120b8b3a568` | `8f632b5c5e48446b9d5502830bf875a5` | 493 pass / 3 skip / 0 fail |
| P0.3 Recovery core | `ef55188d86b8409096354a56241b3971` | `0ed226510b8c469683dfe193df7de77a` | 35/35 PASS; core/focused only |
| production dependency audit | `4294a5325b23491683f682a4349dfcf4` | `77bade90a0f14742a9f03dcb22c174c5` | 0 production vulnerabilities |
| package provenance affected by stale resident runtime | `776a18b744aa4dda83ec3a7ca2986d65` | historical affected waves | artifact checks passed but clean live provenance was withheld at that checkpoint |
| S6/W7 capability/secret foundation | `5e7915c474714154b7ac0f89a43f741d` | `1f74ab333f94410da7d263ddc101516b` | 6/6 focused proofs PASS; full isolated worker gate remained closed |
| S7 trace/runtime closeout | `57807dae8bf94b578d78ab96d7f3b135` | `21a29a1b540d4d99a43676293ee6cf3f` | accepted trace/task/process lifecycle evidence |
| W8/W12 defer gate | `399d5420e538444eb618fc72eb65487f` | `89865d70f047498f85acc318637f32aa` | accepted fail-closed/defer decision |
| W14/W15 final S9 | `4fb70ab0823148af83ff006f6203cb57` | `528e57a47d6a4f348eb62b678a4ea474` | W14 21/21 solution-economics PASS; A2A deferred |

---

# 20. TRACEABILITY METHOD

## 20.1. Audit a current capability claim

For a claim such as “mutation coordination is closed”:

1. inspect current maintained `CURRENT_STATE.md` and current source/runtime if operating now;
2. identify the historical accepted capability/workstream in this master;
3. find the historical accepted source fingerprint;
4. retrieve the relevant RUN/WAVE/proof from the durable ledger;
5. compare current source with the historical accepted fingerprint;
6. if source moved, old proof remains historical only; run the smallest current proof needed for the present claim.

## 20.2. Audit a historical failure

Example: W1 false-green.

```text
historical claim
 -> historical RUN/WAVE
 -> historical source/workspace fingerprint
 -> observed failing proof semantics
 -> later corrective source/proof
 -> permanent invariant/test
```

Do not turn “failed at historical checkpoint” into “currently broken”.

## 20.3. Audit an accepted proof

Use:

```text
claim
 -> capability/workstream
 -> effective wave objective
 -> base/source/worktree fingerprint
 -> RUN
 -> WAVE
 -> proof ID(s)
 -> acceptance/checkpoint
 -> later superseding source if any
```

The addition of **effective wave objective** is mandatory after the objective-provenance fix.

## 20.4. Audit an upstream-derived implementation

Use:

```text
local capability
 -> R0–R5
 -> upstream repo/commit/PR/path
 -> upstream tests
 -> local destination
 -> local adapter/authority delta
 -> boundary tests
 -> EOCL run/wave
 -> accepted source fingerprint
```

## 20.5. Distinguish time dimensions

Always identify:

- historical source time;
- proof time;
- runtime activation time;
- package-build time;
- release/publish time.

A commit timestamp cannot establish the other four.

---

# 21. DECISION LOG

## D-2026-08-20-01 — one checkout / one writer

**Decision:** one canonical checkout; one source writer at a time.  
**Reason:** prevent cross-client contention and ambiguous ownership.  
**Status:** permanent invariant.

## D-2026-08-20-02 — candidate/shadow no-write

**Decision:** candidate/shadow lanes cannot silently direct-apply/commit/promote.  
**Status:** retained.

## D-2026-08-20-03 — false-green proof hardening

**Decision:** exact source/test identity and real execution are required; filtered exit code alone is insufficient.  
**Trigger:** W1 zero-match incident.  
**Status:** permanent invariant.

## D-2026-08-21-01 — S1–S9 architecture/control closure

**Decision:** broad architecture program is terminal for the accepted baseline; deferred capability gates remain explicit.  
**Status:** retained.

## D-2026-08-21-02 — cross-session ownership request-scoped/explicit

**Decision:** unowned commands cannot inherit another globally projected run/wave.  
**Trigger:** real provenance-contamination incident.  
**Status:** accepted source behavior; later source must preserve it.

## D-2026-08-21-03 — upstream-first reuse

**Decision:** R0 COPY -> R1 COPY+ADAPTER -> R2 PORT -> R3 REIMPLEMENT -> R4 DEFER -> R5 REJECT.  
**Reason:** divergent history does not justify duplicate local implementation.  
**Status:** current engineering doctrine.

## D-2026-08-21-04 — consolidate overlapping research plans

**Decision:** preserve one master research/strategy/history narrative rather than multiple overlapping active research plans.  
**Status:** retained.

## D-2026-08-21-05 — master is doctrine/history, not sole operational truth

**Decision:** this dated master no longer claims priority over current source/runtime/EOCL/`CURRENT_STATE.md`/`ROADMAP.md`.  
**Reason:** a file that also preserves history cannot safely act as the sole live status projection.  
**Status:** effective in this reconciled edition.

## D-2026-08-21-06 — P0.3 split into three claim planes

**Decision:** distinguish focused Recovery core, production F1–F9 fault matrix, and reboot/logon persistence.  
**Reason:** eliminate contradictory CLOSED/PENDING semantics across docs.  
**Status:** effective.

## D-2026-08-21-07 — causal hardening replaces G0–G7 literal roadmap

**Decision:** implement Truth Reconciliation -> Wave Objective Provenance -> TruthSnapshot -> Truth Console -> Casebook -> STOP/EVALUATE.  
**Reason:** existing source already contains most G0–G7 foundations; broad implementation would duplicate authority/framework.  
**Status:** recommended plan.

## D-2026-08-21-08 — registry-on-touch

**Decision:** do not build a complete upstream registry until actual upstream maintenance/reuse occurs.  
**Reason:** avoid CMDB-like stale bureaucracy and default context overhead.  
**Status:** recommended policy.

---

# 22. RISK REGISTER

## R1 — Documentation truth conflict

**Risk:** two maintained documents use the same phase label for different claim planes.  
**Control:** Sequence 1 Truth Reconciliation + exact claim-plane naming.

## R2 — Stale wave objective

**Risk:** proof correct but report semantics wrong after REPLAN.  
**Control:** Sequence 2 effective wave objective identity.

## R3 — UI false confidence

**Risk:** ONLINE/READY shown as if source/workspace/package were proven.  
**Control:** TruthSnapshot states + separate transport/provenance presentation.

## R4 — Duplicate authority

**Risk:** identity/truth/upstream subsystem accidentally becomes a second controller.  
**Control:** projections only; EOCL/Recovery remain owners.

## R5 — Registry staleness

**Risk:** full capability inventory becomes stale bureaucracy.  
**Control:** registry-on-touch and compact path-scoped projection.

## R6 — Context/token inflation

**Risk:** governance metadata is injected into every task.  
**Control:** project only the one relevant capability record when selected paths intersect it.

## R7 — Historical proof reused for newer source

**Risk:** old green proof is presented as current.  
**Control:** exact fingerprint binding; source/proof/live/package/release separated.

## R8 — Package truth fabricated from source identity

**Risk:** Git HEAD is treated as package manifest.  
**Control:** package identity requires package/resource evidence; otherwise UNKNOWN/N/A.

## R9 — Cross-session projection confusion

**Risk:** UI/task projection includes foreign semantic activity and is mistaken for write ownership.  
**Control:** TruthSnapshot + explicit owner/run/wave evidence; never infer authority from projection alone.

## R10 — Casebook becomes another platform

**Risk:** project builds a generic replay system rather than regressions.  
**Control:** existing test frameworks only until a proven limitation exists.

---

# 23. STOP CONDITIONS

Engineering should stop the hardening program when:

- effective wave objective is reliably auditable;
- source/runtime/workspace/package/evidence truth can be composed fail-closed;
- operator UI clearly separates transport from provenance;
- major historical incidents have deterministic regression coverage;
- no current defect or consumer justifies another governance layer.

Do not continue merely to maximize completeness scores.

A later capability opens only with a new material trigger.

---

# 24. DOCUMENT MAINTENANCE RULES

## 24.1. Keep one research consolidation narrative

Do not recreate separate overlapping active files for:

- current strategy;
- closure;
- upstream-reuse plan;
- the same implementation program.

Append/reconcile here when the subject is historical doctrine or audit narrative.

## 24.2. Keep operational truth in maintained docs

If implementation acceptance changes current behavior:

- update `docs/CURRENT_STATE.md`;
- update `docs/ROADMAP.md` if priorities/gates change;
- update relevant release/security/recovery docs when their claim boundary changes.

Do not expect a dated research master to replace these roles.

## 24.3. Preserve chronology

When a claim changes:

- update the current maintained truth;
- append a dated decision/checkpoint here if historically material;
- preserve old run/wave/proof IDs;
- mark superseded interpretation rather than erasing it.

## 24.4. Never persist private reasoning

Record only:

- objective;
- effective wave objective;
- authority;
- state;
- source identity;
- proof identity;
- decision;
- outcome;
- material risk;
- next action.

## 24.5. Durable ledger remains canonical execution history

This Markdown is an index/narrative. It never replaces `.coding-tools/orchestration/ledger.sqlite3` and generated run/wave evidence.

---

# 25. FUTURE CHECKPOINT TEMPLATE

```text
CHECKPOINT: <capability/workstream>
TIME: <ISO-8601 + timezone>
STATUS: PLANNED | ACTIVE | REPLAN | ACCEPTING | ACCEPTED | BLOCKED | DEFERRED | SUPERSEDED
BASE HEAD: <sha>
SOURCE/WORKTREE FP: <fingerprint>
RUN/WAVE: <ids>
RUN INITIAL OBJECTIVE: <text/hash>
WAVE EFFECTIVE OBJECTIVE: <text/hash/revision>
UPSTREAM: <repo/pr/commit if applicable>
REUSE MODE: R0 | R1 | R2 | R3 | R4 | R5 | N/A
CHANGED: <paths/surfaces>
PROOF: <ids + exact outcomes>
CLAIM PLANE: source | focused-proof | live | package | release
DECISION: <what is now true>
SUPERSEDES: <prior statement if any>
RISKS: <remaining material risks>
NEXT: <one critical action>
```

---

# 26. ONE-PAGE OPERATOR DECISION CARD

```text
A. WHAT IS TRUE NOW?
   -> read live source/runtime/EOCL + CURRENT_STATE
   -> do not infer from dated research alone

B. IS THIS OLD PHASE CLOSED?
   -> keep closed unless a real defect/consumer/security/upstream delta exists

C. IS THERE UPSTREAM IMPLEMENTATION?
   -> R0 COPY first
   -> R1 COPY+ADAPTER if boundary differs
   -> R2 PORT if runtime/language requires it
   -> R3 REIMPLEMENT only with written evidence
   -> R4/R5 if no value or architectural conflict

D. IS THE UI GREEN?
   -> ONLINE != MATCHED
   -> require TruthSnapshot evidence

E. DID REPLAN CHANGE THE GOAL?
   -> bind new effective wave objective
   -> keep run initial objective as history

F. IS PACKAGE/RELEASE CLAIMED?
   -> require exact package/release evidence
   -> source proof is not enough

G. SHOULD WE BUILD ANOTHER FRAMEWORK?
   -> only if a concrete defect/consumer proves the current primitive cannot solve it
   -> otherwise STOP
```

---

# 27. FINAL STATUS CARD

```text
BROAD ARCHITECTURE PROGRAM
  S1–S9 terminal for the historical accepted baseline

CURRENT STRATEGIC PROBLEM
  truth + traceability hardening, not architecture accumulation

FIRST REQUIRED STEP
  reconcile current truth/claim planes

FIRST RECOMMENDED SOURCE PATCH
  effective wave objective provenance

NEXT BACKEND DELTA
  TruthSnapshot read-only projection

NEXT UI DELTA
  Operator Truth Console

HISTORICAL LEARNING SYSTEM
  Executable Casebook using existing test frameworks

UPSTREAM GOVERNANCE
  R0 -> R1 -> R2 -> R3 -> R4/R5
  registry-on-touch only

PUBLIC TOOL SURFACE
  keep smart-v3 = 8 unless explicitly changed

MUTATION AUTHORITY
  one writer through EOCL/write lease

P0.3
  core/focused CLOSED
  production fault matrix separate
  reboot/logon persistence separate

NATIVE SEMANTIC
  NATIVE_LSP_BINDING_NOT_CONFIGURED unless live maintained truth changes

PROHIBITED
  second ledger / second identity authority / generic evidence system /
  G0–G7 literal rebuild / full upstream CMDB / automatic promotion without evidence
```

---

# FINAL STATEMENT

> **Coding Web does not need another broad architecture expansion. The accepted architecture should be preserved, not reopened. The next engineering program is deliberately narrow: reconcile truth, make wave intent auditable, compose existing identity into a fail-closed TruthSnapshot, expose that truth to the operator, and convert the most expensive historical mistakes into deterministic regression cases. Upstream work remains copy-first but only when a real capability is touched; governance metadata remains small and path-scoped. Historical runs, waves, proofs and source identities are preserved here for forensic traceability, while current operational truth remains owned by the live source/runtime/EOCL and maintained product documents. This separation is the final control against both information pollution and overengineering.**
