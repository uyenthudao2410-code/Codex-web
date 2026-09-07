# Orchestration Run Summary

- Run: `f7f34289300d42dda4a8d556a8183459`
- Task: `1cce6676335c42f48c1caaa1cefe0b0f`
- Objective: Implement the user-authorized bounded exact-stale maintenance seam in Recovery Host full-clean replacement. Parse only a strict reserved reason prefix exact_stale_runs:<comma-separated 32-lowerhex-run-ids>, max 16 unique IDs. In continueReplacement, while the old canonical Coding MCP is already stopped and before orchestrator.start, sequentially run the existing reconcile_exact_stale_run.py through pythonStatus/execFile without shell: fresh preflight per ID, validate physical+logical HEX64 snapshot hashes, then reconcile with --runtime-stopped and exact expected hashes; require schema_version=1, reconciliation.chain_ok=true, and postflight target stale/RECONCILED_STALE/already_reconciled=true. Any malformed request, Python/script failure, receipt mismatch, or deadline expiry must fail the activation closed before MCP start. Ordinary restart reasons remain unchanged/no-op. Add focused tests proving sequential maintenance occurs before MCP start and malformed reserved reasons prevent start. Do not change public MCP tool schema/count, Python ledger logic, unrelated source, Git history, or external services.
- Status: **accepted**
- Started: `2026-09-07T02:55:36.242Z`
- Finished: `2026-09-07T03:18:49.392Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `43cf4f035d2542e0ae12f0c966ed9237` | 1 | `run_initial_objective` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 2 | `9ae16cad015d409899cde342eece012f` | 1 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 3 | `c4c108c0cf8945aea7d3e8d7854e222e` | 1 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 24b489bbb0ba49b5a49bf88008803180 | c4c108c0cf8945aea7d3e8d7854e222e | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | 2d6f358f5957f62c2f8f4ec0e5804122b6cc8fbf4b8a0e94d03dc2bb04866f40 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 42981 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 43016 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 43050 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 43006 | `SOL_REJECTED` | `ACCEPTING` | Focused suite is 47/49: both new exact-stale tests fail before the maintenance seam because their test clock/deadline is already expired. Production patch is not accepted; replan only the test fixture clock/deadline. |
| 43041 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance failed closed with ACCEPTANCE_FILE_ATTESTATION_REQUIRED: one pre-existing dirty acceptance path (fullCleanActivation.js from the prior rejected wave) is not yet proven inside this wave's durable mutation surface. Code/test oracle is green; replan solely to exact-byte adopt current fullCleanActivation.js and test bytes into a fresh wave, rerun the same proofs, then accept. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `100`
- Chain head: `d131d7d6fc7b04b21d22ab14c6e56caacc5eaa3ccda8de8ab8f99f6586968fad`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
