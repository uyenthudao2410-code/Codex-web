# EOCL Implementation & Deployment Record

**Date:** 2026-08-13  
**Repository:** `uyenthudao2410-code/Tools-Codex-web`  
**Implementation commit:** `42e6737d8440bdaf9dd13a73a6f7367143fdd12e`  
**Commit message:** `feat: enforce orchestration audit control loop`  
**Design record:** `docs/research/ORCHESTRATION_WAVE_AUDIT_LEDGER_AND_OPTIMAL_ROLLOUT_PLAN_2026-08-13.md`

---

## 1. Deployment outcome

The EOCL/audit design has been implemented in Coding Tools MCP without changing the established model hierarchy or increasing the public smart tool surface.

Production model policy remains:

```text
CONTROL                  ChatWeb Sol
DETERMINISTIC            Coding Tools MCP
CHEAP PATCH              Mini low / no-tools
HARDER LEAF              Luna high / no-tools
DEEP CODE                Codex Sol xhigh
CROSS-FILE EXPERIMENT    Terra high
CONSEQUENTIAL            Sol max
PARALLEL EXTREME         Sol ultra
FINAL ACCEPTANCE         ChatWeb Sol + deterministic evidence
```

The implementation changes execution accountability rather than model selection.

---

## 2. Source delivered

Implementation commit contains exactly 13 Coding Tools MCP/test files and does not include the unrelated pre-existing Rust/WebCodex working-tree changes.

New runtime modules:

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py
resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_report.py
```

Modified runtime modules:

```text
resources/coding-tools-mcp/coding_tools_mcp/server.py
resources/coding-tools-mcp/coding_tools_mcp/task_state.py
resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py
```

New tests:

```text
resources/coding-tools-mcp/tests/test_orchestration_ledger.py
resources/coding-tools-mcp/tests/test_orchestration_control.py
resources/coding-tools-mcp/tests/test_proof_ledger.py
resources/coding-tools-mcp/tests/test_orchestration_report.py
resources/coding-tools-mcp/tests/test_orchestration_workflow.py
```

Extended existing test:

```text
resources/coding-tools-mcp/tests/test_task_state_and_build.py
```

Commit stats observed at creation:

```text
13 files changed
2733 insertions
97 deletions
```

---

## 3. Canonical audit ledger

Each workspace now owns a durable SQLite audit database:

```text
.coding-tools/orchestration/ledger.sqlite3
```

The ledger stores first-class entities for:

```text
RUN
WAVE
DELEGATION
EVENT
PROOF
CHECKPOINT
```

Events are append-only and hash-chained per run with `prev_hash` and `event_hash`. The runtime can verify the chain to detect accidental event loss/reordering.

The ledger intentionally does not store raw private chain-of-thought. Sensitive payload keys are redacted; prompt/content/patch/stdout/stderr-like values are represented by bounded metadata and SHA-256 identities rather than raw text where audit identity is sufficient.

---

## 4. EOCL state machine

Implemented states:

```text
PREFLIGHT
READY
ROUTED
EXECUTING
PROVING
ACCEPTING
CHECKPOINTED
REPLAN
BLOCKED
ABORTED
```

Normal path:

```text
PREFLIGHT -> READY -> ROUTED -> EXECUTING -> PROVING -> ACCEPTING -> CHECKPOINTED
```

Hard enforcement includes:

```text
NO ROUTE CHANGE WITHOUT STATE TRANSITION
NO WRITE OWNER CHANGE WITHOUT OWNERSHIP TRANSFER
NO IMPLEMENTATION WRITE WITHOUT ACTIVE WRITE LEASE
NO PROOF REUSE WITHOUT FINGERPRINT MATCH
NO PARALLEL AUTHORITATIVE WRITER ON ONE WORKTREE
```

A failure entering `REPLAN`, `BLOCKED`, or `ABORTED` revokes the active write lease.

---

## 5. Write authority

Runtime write leases carry:

```text
lease_id
owner
mode
base_head
worktree_fp
allowed_paths
delegation_id
```

Before authoritative MCP mutation, runtime checks:

- state is `EXECUTING`;
- an active lease exists;
- owner matches;
- base HEAD still matches;
- worktree fingerprint still matches;
- candidate-lane path scope remains inside the allowed set when supplied.

Candidate-only Mini/Luna delegation does not grant authoritative write ownership. MCP remains the writer/proof authority.

---

## 6. Explicit REPLAN

A failed implementation lane does not silently degrade into controller-led patches.

Examples normalized into typed recovery include:

```text
SUPERVISOR_NOT_READY
PROMPT_TOO_LARGE
DEADLINE
CAPACITY
BASE_DRIFT
PATCH_AMBIGUOUS
PATCH_CONTEXT_NOT_FOUND
CONTRACT_DRIFT
PROOF_TIMEOUT
```

A run in `REPLAN` requires a concrete `replan_reason` before a replacement wave can begin. The new wave keeps the same run lineage but gets a new wave identity, allowing failed-attempt cost and recovery to be measured rather than erased.

---

## 7. Execution modes

EOCL source schema now includes:

```text
auto
mcp_only
bounded_candidate
deep_single_lane
coordinated_multi_worktree
```

Current fail-safe behavior:

- `mcp_only` requires deterministic routing.
- `bounded_candidate` requires Mini/Luna candidate routing.
- `deep_single_lane` defaults an otherwise-auto deep route to Sol xhigh.
- `coordinated_multi_worktree` is **not silently emulated**. Until a verified production supervisor adapter is registered, execution returns `SUPERVISOR_NOT_READY` and moves to `REPLAN`.

This deliberately fixes the PFM incident class where coordination infrastructure existed but was not live and the controller continued implementation anyway.

---

## 8. Proof ledger and resumability

Proof identity includes the execution inputs that affect validity, including:

```text
stage_id + stage_version
base_head
worktree_fp
contract_fp
relevant source/config content fingerprint
command/config identity
upstream proof ids
```

When the exact fingerprint already has a valid PASS, the runtime may reuse it. Source/config/base/contract changes invalidate reuse.

This supports the desired verification policy:

```text
focused packet proof
-> affected boundary proof
-> broad authority once on final integrated fingerprint
```

A timeout in a later proof stage does not erase already-valid earlier proof.

---

## 9. Final acceptance is now an explicit state transition

`agent_workflow` success no longer means the orchestration run is automatically completed.

After deterministic proof, the run reaches:

```text
ACCEPTING
```

The source schema adds `task_control` actions:

```text
audit
accept
reject
```

`accept` is legal only from `ACCEPTING`, records ChatWeb Sol final acceptance/checkpoint metadata, and transitions to:

```text
CHECKPOINTED
```

`reject` requires a reason and transitions the same run to:

```text
REPLAN
```

This prevents a proven patch from being conflated with semantic/governance acceptance.

---

## 10. Generated audit reports

Runtime can generate human-readable projections from the canonical database:

```text
.coding-tools/orchestration/reports/run-<run-id>/run-summary.md
.coding-tools/orchestration/reports/run-<run-id>/wave-001.md
...
```

Reports include:

- run/wave/base/contract identity;
- delegation and authority ownership;
- requested/resolved route/model/effort;
- state timeline;
- failures and REPLAN causes;
- proof stages/fingerprints/cache hits;
- hash-chain integrity;
- durable acceptance checkpoints, accepted Git HEAD, proof fingerprint, and acceptance authority.

These generated files are operational state/evidence. They are not automatically project source and should not be committed unless project policy explicitly requires it.

---

## 11. Current-state and performance projections

`task-state.json` remains for current UI/session state and backwards compatibility but now carries an `orchestration` projection. It is not the history authority.

`performance.json` remains a lightweight performance view and now associates calls with `run_id`, `wave_id`, and `delegation_id` where available. It is not used as the canonical causal timeline.

Existing anonymous product telemetry remains privacy-constrained and separate from the audit ledger.

---

## 12. Test evidence

The original EOCL integration passed 53/53 Python tests and 5/5 Node stability tests. Follow-up corrective waves added checkpoint-summary/report coverage and the final local acceptance gate observed:

```text
Python: 56/56 PASS
Node stability: 5/5 PASS
git diff --check: PASS
```

The corrective work additionally covered:

- in-memory EOCL wave snapshot persistence across transitions/replan;
- recovery to the current wave after process boundary;
- durable checkpoint listing in audit summaries;
- checkpoint provenance in generated run/wave Markdown reports.

---

## 13. Runtime topology correction

Early deployment notes treated port `18765` as the production native backend. Final runtime inspection corrected that assumption.

The active Desktop-managed backend is:

```text
127.0.0.1:18766
parent: electron.exe
workspace: E:\DEV\Tools-Codex-web
permission mode: safe
tool mode observed by connector: smart
```

The Electron-managed process was observed starting after the final source HEAD and had an established local connection to the tunnel/client.

A separate `18765` instance was an orphan process left from manual restart experiments. It had no established client connection and was terminated. Final `netstat` showed only `18766` listening.

This correction is important operationally: **Electron-owned 18766 is authoritative for the Desktop/tunnel path; manual orphan listeners must not be mistaken for production simply because they bind the older port.**

---

## 14. Live end-to-end EOCL acceptance

A live deterministic production smoke ran through the active connector with no project-source mutation.

Observed route/state:

```text
route_resolved = deterministic
execution_mode = mcp_only
PREFLIGHT -> READY -> ROUTED -> EXECUTING -> PROVING -> ACCEPTING
```

Deterministic proof:

```text
command: cmd /d /c echo EOCL_LIVE_SMOKE_OK
status: passed
```

Observed run:

```text
run_id  = 5757d8ea9440481fb69f1ac78571dfa3
wave_id = eaa6e51b79384ba784f444bfff771d75
```

Final acceptance was recorded through the EOCL runtime API against the same durable ledger. A fresh Runtime recovered the run as:

```text
STATE=CHECKPOINTED
INTEGRITY_OK=True
EVENTS=15
PROOFS=1
CHECKPOINTS=1
CHECKPOINT_STATUS=accepted
CHECKPOINT_HEAD=83581b4f262846a3c8b0daadb7417391702e5fb3
```

This proves final acceptance survives a process boundary and is not only an in-memory state.

A second corrective EOCL wave that added checkpoint export/reporting also reached `CHECKPOINTED`; its audit showed one accepted checkpoint with proof fingerprint and integrity `True`.

---

## 15. Follow-up corrective commits

The EOCL implementation was hardened by the following additional commits:

```text
83581b4f  fix: persist EOCL wave state transitions
387308c0  fix: preserve terminal EOCL task projection
ec91b82e  fix: include EOCL checkpoints in audit summaries
bd87d8bc  feat: render EOCL acceptance checkpoints in reports
```

Final source HEAD at deployment acceptance:

```text
bd87d8bc5c2b1c25f9f9fe5fe3dcb46b29e78fe8
```

`origin/main` was observed at the same SHA.

---

## 16. Skill v5 final installation status

`sol-lean-codex` v5 is active in ChatWeb resource discovery and installed globally on Windows.

ChatWeb resource discovery observed 14 skill files including:

```text
references/eocl-runtime.md
```

Windows global installation:

```text
C:\Users\Admin\.codex\skills\sol-lean-codex
FILE_COUNT=14
SKILL.md SHA-256=C62B34ED36930D679B4D0C3DD01B2D2E50D864C1BD88E34EF8BBFF8E9DA034D2
route-policy comparator=10/10 PASS
```

Backup retained:

```text
C:\Users\Admin\.codex\skills\sol-lean-codex.SKILL-pre-v5-20260813.md
```

The validated package remains archived in ChatGPT Library under:

```text
/Codex Orchestration/sol-lean-codex-v5-skill.zip
```

Package SHA-256 used during validation:

```text
858632ab57fe58c07083f2a1344b8169bad54a28a4947c6a11cf934a4159aa87
```

---

## 17. Client schema-cache status

The active server source exposes manual EOCL actions/fields (`audit`, `accept`, `reject`, execution-mode controls), but the **current conversation's preloaded function schema still shows the older task_control enum**. This is a client-session schema cache limitation, not a server/runtime deployment failure.

Important distinction:

```text
SERVER/BACKEND EOCL: ACTIVE
CHATWEB SKILL V5: ACTIVE
WINDOWS GLOBAL SKILL V5: ACTIVE
CURRENT CONVERSATION MANUAL ACTION ENUM: STALE CACHE
```

Server-side auto routing and EOCL enforcement are active now. Manual `task_control accept/reject/audit` from the typed function surface should be expected to appear after a fresh ChatWeb conversation/tool-schema discovery. The live final acceptance above was intentionally performed through the same EOCL runtime API and durable ledger rather than pretending the stale client enum exposed an action that it did not.

---

## 18. Deployment acceptance matrix — final observed state

| Layer | Status | Evidence |
|---|---|---|
| EOCL source | DEPLOYED | implementation `42e6737d` plus corrective commits through `bd87d8bc` |
| GitHub `main` | PUSHED | local HEAD and `origin/main` observed at `bd87d8bc5c2b1c25f9f9fe5fe3dcb46b29e78fe8` |
| Full Python suite | PASS | 56/56 final local gate |
| Node stability suite | PASS | 5/5 final local gate |
| Diff hygiene | PASS | scoped `git diff --check` |
| Public 8-tool smart surface | PRESERVED | connector still discovers 8 smart tools |
| Active Desktop MCP backend | ACTIVE | Electron-managed `127.0.0.1:18766` |
| Orphan manual backend | REMOVED | `18765` process terminated; final listener check showed only 18766 |
| Live EOCL state path | PASS | production smoke reached `ACCEPTING` |
| Durable final acceptance | PASS | fresh runtime recovered `CHECKPOINTED`, integrity OK, proof + checkpoint present |
| Checkpoint audit export | PASS | `checkpoints[]` contains accepted provenance |
| Checkpoint Markdown reports | PASS | focused + full tests; commit `bd87d8bc` |
| Skill v5 package | VALIDATED | 14 files, package SHA above |
| Windows global skill v5 | INSTALLED | 14 files, SKILL SHA `C62B34...034D2`, comparator 10/10 |
| ChatWeb skill v5 | ACTIVE | v5 resource tree including EOCL runtime reference |
| Current-conversation manual EOCL schema | STALE CLIENT CACHE | server source is new; current typed enum was prefetched before refresh |
| GitHub Actions for final HEAD | IN PROGRESS AT RECORD UPDATE | run `31671263347`; no failure observed at update time |

---

## 19. Final operational status

The system is production-ready for **server-enforced automatic orchestration** under the current ChatWeb + Coding Tools MCP path.

For new work, the effective architecture is:

```text
ChatWeb Sol
  -> Coding Tools MCP / EOCL
     -> deterministic / Mini / Luna / Sol xhigh according to policy
     -> explicit Terra/Max/Ultra gates only
  -> proof fingerprint + audit ledger
  -> ACCEPTING
  -> ChatWeb Sol final acceptance
  -> CHECKPOINTED
```

The only remaining session-local limitation is display/invocation of newly added manual EOCL arguments through the current conversation's cached function schema. This does **not** disable server-side EOCL enforcement or automatic routing. A fresh ChatWeb conversation/tool discovery is the correct way to refresh those manual fields; no server rollback or further runtime patch is required for that cache behavior.
