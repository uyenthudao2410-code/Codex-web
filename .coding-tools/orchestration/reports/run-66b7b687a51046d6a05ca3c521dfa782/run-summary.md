# Orchestration Run Summary

- Run: `66b7b687a51046d6a05ca3c521dfa782`
- Task: `8ec966e46e8949c494d37a8e2bd6c85a`
- Objective: Replan Phase 3B after 37/38 focused tests passed but the standalone Recovery MCP test parsed an unexpected HTML response on the dynamically allocated port. Strengthen only the process oracle first: capture the spawned Recovery MCP stderr, require the child PID to still be alive after TCP readiness, GET /healthz from the same port and assert service='recovery-mcp' and pid==child.pid before making authenticated MCP requests. Make the generic HTTP helper preserve raw non-JSON bodies in assertion errors instead of throwing JSON.parse. Do not weaken Recovery MCP production behavior or auth assertions. Rerun py_compile and focused recovery-plane test.
- Status: **accepted**
- Started: `2026-08-16T08:55:18.766Z`
- Finished: `2026-08-16T09:14:13.878Z`

## Outcome metrics

- Waves: **7**
- Route decisions: **7**
- Failures observed: **7**
- REPLAN transitions: **7**
- Proof stages: **28**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `846a562c58ba4296abd9c2312502349b` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 2 | `06ee0c6bf71f4d2db6d472ccd450a90a` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 3 | `3313021bd0b7405380c16746dfd9f005` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 4 | `2b49861cfa944c5193d283c5a45c1fd7` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 5 | `464c49c6d5844d7fa6ca6dfa968a3fbf` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 6 | `a346e197e9c74aa680c5b2c7e9929b45` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 7 | `3b72d298faab4f6887950687332343af` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7697ba5b800045e785dd9df46c761ba9 | 3b72d298faab4f6887950687332343af | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 9e781679fb18c7c2237e9437b93d6cc04304510cf4e4f14f50271860183cbeca | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 6489 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6511 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6544 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6580 | `deterministic` | `deterministic` | explicit_request |
| 6640 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6687 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6725 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 6505 | `CHECK_FAILED` | `PROVING` |  |
| 6538 | `CHECK_FAILED` | `PROVING` |  |
| 6566 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 6574 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |
| 6632 | `SOL_REJECTED` | `ACCEPTING` | Source/proof quality is good, but final acceptance provenance is incomplete: the current run's task-state modified_files records only tests/recovery-plane.test.js and resources/recovery-mcp/recovery_mcp.py, while core Phase 3B Recovery Host/config/runtime source was first changed in an earlier failed run. Accepting this wave would create canonical receipts for only part of the bytes and the V2 auto-activation gate would correctly block the remaining dirty component paths. Replan a final bounded provenance wave that materially touches all Phase 3B runtime source and re-proves the exact final fingerprint. |
| 6681 | `SOL_REJECTED` | `ACCEPTING` | Do not activate yet. Final provenance now covers 8 Phase 3B files but still omits resources/recovery-mcp/recovery_mcp.py, so its final accepted SHA receipt would be missing. Also, review found a fail-closed lifecycle edge: if a previously running Recovery Tunnel becomes not_configured, shares the primary tunnel ID, or loses its Runtime API key, ensureTunnel currently reports blocked/not_configured but can leave the old service-owned Recovery Tunnel PID alive. Replan to include Recovery MCP Python in final receipt scope and explicitly stop/null a stale owned Recovery Tunnel on invalid configuration, then re-prove. |
| 6719 | `SOL_REJECTED` | `ACCEPTING` | Behavior/proof is green, but task-state still does not list resources/recovery-mcp/recovery_mcp.py in modified_files after the background workflow completed. Do not accept a checkpoint that cannot issue a canonical receipt for the Recovery MCP runtime. Replan one small Recovery-MCP-only contract wave that adds a useful snapshot schema marker and records the Python path explicitly; reuse prior green JS/service proof only where source is unchanged. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `271`
- Chain head: `6e3848c269d200d6fca4d0162b782332078ef865e4cd623aea8368f5fef0422d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
