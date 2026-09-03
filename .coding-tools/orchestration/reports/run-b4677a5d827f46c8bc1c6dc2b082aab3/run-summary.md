# Orchestration Run Summary

- Run: `b4677a5d827f46c8bc1c6dc2b082aab3`
- Task: `8af545fbcc794abb84a767f2deb4e7ec`
- Objective: Continue WAVE 2 of the active recovery RUN. Fix only the newly exposed public tool-call exception-boundary defect: observability correlation in Runtime._tool_invocation_context must not let a request-bound ToolFailure escape before Runtime.call_tool can normalize the authoritative workspace-scope failure. Treat task-state lookup only as best-effort invocation metadata by catching ToolFailure and using empty task/orchestration metadata; do not catch generic exceptions and do not weaken _set_request_workspace_scope or UNKNOWN_LEGACY_WORKSPACE enforcement. Preserve the already-proven broker cwd fix and all unrelated dirty work. Run focused workspace-session isolation plus invocation-trace tests, then npm run test:all. No commit, push, restart, package, publish, release, or deploy.
- Status: **accepted**
- Started: `2026-09-02T06:33:27.344Z`
- Finished: `2026-09-02T07:22:48.144Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f4b76c206f434752879da64217ea41a3` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `7a676aa9cea64373837ee93102b3f4c2` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `ce462c8c016f4077abc26654b3a48814` | 3 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 9f1566903d2a4ede92d8caa091115d25 | ce462c8c016f4077abc26654b3a48814 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 13ae1d09a88b1f9ec45c3eedfa3392e8a4e34580f0788932a4d923b81668e116 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 35426 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 35450 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 35506 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 35441 | `CHECK_FAILED` | `PROVING` |  |
| 35499 | `SOL_REJECTED` | `ACCEPTING` | COMPLETE_CURRENT_ACCEPTANCE_SCOPE_NOT_DURABLY_ATTESTABLE: fresh current activation census from baseline 3a3abaff72a8e6382e4c362865becba069e4ecfc requires recovery_host/coding_mcp/electron_ui component receipts beyond this wave's durable authority. WAVE 7a676aa9cea64373837ee93102b3f4c2 acquired a write lease whose allowed_paths contained only resources/coding-tools-mcp/coding_tools_mcp/server.py, while its existing_dirty_source_paths include other current bytes such as electron/services/processIdentity.js, tests/process-identity.test.js, coordination.py, problem_lineage.py and usage_reservations.py. The acceptance guard requires any explicitly attested pre-existing dirty path to be in this wave's durable patch/adoption surface; a complete current packet would therefore fail ACCEPTANCE_FILE_ATTESTATION_REQUIRED. Preserve all current source bytes and both green proofs; replan to exact-byte no-write adoption of the still-untrusted current dirty acceptance surface, then accept the complete current component packet without rerunning unchanged proof where cache evidence is available. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `78`
- Chain head: `d7293f6aaed042a4c00f637dae00b40d025f3d3a99346472e083ffb62703f04d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
