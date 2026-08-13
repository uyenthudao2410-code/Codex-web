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
- hash-chain integrity.

These generated files are operational state/evidence. They are not automatically project source and should not be committed unless project policy explicitly requires it.

---

## 11. Current-state and performance projections

`task-state.json` remains for current UI/session state and backwards compatibility but now carries an `orchestration` projection. It is not the history authority.

`performance.json` remains a lightweight performance view and now associates calls with `run_id`, `wave_id`, and `delegation_id` where available. It is not used as the canonical causal timeline.

Existing anonymous product telemetry remains privacy-constrained and separate from the audit ledger.

---

## 12. Test evidence

Before final commit, the following was observed on the native Python runtime shipped by the project:

```text
resources\native-python\python.exe -m unittest discover -s resources\coding-tools-mcp\tests -p test_*.py
```

Result:

```text
Ran 53 tests
OK
```

This includes the previous 44-test suite plus new tests covering:

- SQLite event persistence across restart;
- audit hash-chain integrity;
- sensitive audit-payload redaction;
- state-transition legality;
- write-owner enforcement;
- lease revocation on failure;
- REPLAN/new-wave lineage;
- active-state recovery;
- proof cache reuse;
- proof invalidation after source change;
- generated Markdown reports;
- coordinated-mode not-ready -> REPLAN;
- explicit replan reason requirement;
- `ACCEPTING -> task_control accept -> CHECKPOINTED`;
- reject-reason requirement and `ACCEPTING -> REPLAN`.

Source-stability suite:

```text
node --test tests\stability-source.test.js
```

Result:

```text
5/5 PASS
```

Also observed:

```text
git diff --cached --check
PASS
```

---

## 13. Windows runtime reload

Before reload, native MCP was observed listening at:

```text
127.0.0.1:18765
PID 28464
```

A first reload came up as PID `22888` but omitted two required environment settings, revealing an important startup invariant: runtime defaults to coding tool mode and no additional authorized root if the environment is not carried forward.

The server was therefore restarted again with:

```text
CODING_TOOLS_MCP_TOOL_MODE=smart
CODING_TOOLS_MCP_AUTHORIZED_ROOTS=E:\DEV\Tools-Codex-web
```

and the existing safe permission mode/workspace:

```text
--workspace "E:\DEV\HR STA\HR"
--host 127.0.0.1
--port 18765
--permission-mode safe
```

The corrected native process was observed listening as:

```text
PID 28264
```

An `exec_command` using `E:\DEV\Tools-Codex-web` succeeded immediately after the corrected restart, demonstrating that the Tools authorized root had been restored.

---

## 14. Client-session limitation after native reload

The current ChatWeb MCP tunnel retained a pre-reload session id. After the corrected native restart it returned:

```text
Session terminated
```

and the current ChatWeb wrapper continued to expose the pre-refresh schemas for `agent_workflow` and `task_control`.

Therefore **no claim is made that this same ChatWeb session executed the new manual `execution_mode`, `audit`, `accept`, or `reject` fields after reload**.

The server source implements them and unit/integration tests exercise them. A refreshed/reconnected/new ChatWeb MCP session is required before those new manual fields can be invoked from the client surface. Server-side safe behavior must remain the source of truth; client schema cache is not evidence that a hidden action occurred.

The tunnel/Electron process was intentionally not restarted merely to force schema refresh, avoiding unnecessary blast radius.

---

## 15. Skill v5 synchronization artifact

`sol-lean-codex` was updated after runtime implementation to encode:

- EOCL RUN/WAVE authority;
- explicit state path;
- no second implementation wave while `ACCEPTING`;
- logged ChatWeb Sol accept/reject;
- explicit `replan_reason` after failure;
- write-lease discipline;
- proof fingerprint reuse rules;
- coordinated-mode readiness;
- audit-report use;
- schema-cache honesty;
- prohibition on logging private chain-of-thought;
- route tuning only from durable observed wave history.

Validated package:

```text
skill.zip
14 files
58,701 bytes
SHA-256 858632ab57fe58c07083f2a1344b8169bad54a28a4947c6a11cf934a4159aa87
```

Skill validation:

```text
quick_validate: PASS
route-policy comparator: 10/10 PASS
package_skill validation: PASS
```

The package contains a new reference:

```text
references/eocl-runtime.md
```

### Install status

The v5 package is validated and ready. It was **not written to the Windows global skill directory from the terminated MCP session**, and the current ChatWeb skill library cannot be mutated through the available control-plane tools. Do not report those two client-side installations as completed until a fresh connected session verifies the hashes/resources.

---

## 16. Deployment acceptance matrix

| Layer | Status | Evidence |
|---|---|---|
| EOCL source | DEPLOYED | commit `42e6737d8440bdaf9dd13a73a6f7367143fdd12e` |
| GitHub `main` | PUSHED | `ab89263f..42e6737d` push observed |
| Existing Python regressions | PASS | 44/44 before full integration |
| Full Python suite | PASS | 53/53 after EOCL integration |
| Node stability suite | PASS | 5/5 |
| Diff hygiene | PASS | `git diff --cached --check` |
| Public 8-tool smart surface | PRESERVED | no new public model-facing tools introduced |
| Native MCP corrected restart | OBSERVED | PID 28264 listening after smart/authorized-root env restoration |
| Fresh client schema handshake | PENDING | current tunnel session terminated after native reload |
| Skill v5 package | VALIDATED | 14 files, SHA above |
| Windows global skill v5 install | PENDING CLIENT RECONNECT | cannot mutate host after session termination |
| ChatWeb Skill Library v5 upload/refresh | PENDING | no custom-skill write control available in current tool surface |

---

## 17. Next-session acceptance procedure

On the first fresh MCP-connected ChatWeb session:

1. Verify native listener/runtime is reachable.
2. Verify `agent_workflow` schema exposes `execution_mode`, `replan_reason`, `contract_fingerprint`.
3. Verify `task_control` exposes `audit`, `accept`, `reject`.
4. Run a low-risk fixture workflow:
   - execute known deterministic patch;
   - observe `PREFLIGHT -> READY -> ROUTED -> EXECUTING -> PROVING -> ACCEPTING`;
   - call `task_control audit` and verify hash-chain `ok=true`;
   - call `task_control accept`;
   - verify `CHECKPOINTED` and generated reports.
5. Verify a forced failure enters `REPLAN` and cannot continue without `replan_reason`.
6. Install the validated v5 `skill.zip` into Windows global skill directory using staging/backup/hash verification.
7. Upload/replace the ChatWeb skill with the same package and start a fresh chat so skill resources are rediscovered.
8. Only after these checks treat EOCL manual controls as fully client-deployed.

This procedure intentionally separates **server deployment** from **client-schema/skill activation** so future incident reports cannot collapse them into one ambiguous "deployed" status.
