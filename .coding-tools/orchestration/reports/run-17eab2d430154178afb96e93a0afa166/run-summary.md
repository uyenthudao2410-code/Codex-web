# Orchestration Run Summary

- Run: `17eab2d430154178afb96e93a0afa166`
- Task: `deb439a332fb4f51966a8ee9aa7ce899`
- Objective: M1-BOOTSTRAP-EXPIRY-01: stop retrying an expired no-workspace activation bootstrap. Under an atomic activation-state observation, return ACTIVATION_REQUEST_EXPIRED, ok=false, completed=false, retryable=false, workspace_accessed=false and MCP isError=true at or after a positive startup deadline. Preserve the positive pre-deadline bootstrap, no-workspace dispatch boundary, exact receipt/permission/lease checks, already OPEN runtime behavior, max_lines_per_file and the eight public tool schemas. Write only coding_tools_mcp/activation_lifecycle.py, coding_tools_mcp/server.py, tests/test_activation_epoch.py and tests/test_stateless_http_2026.py inside resources/coding-tools-mcp. Preserve all pre-existing WIP. Run focused expiry/HTTP/trace proofs, stop at ACCEPTING, no final acceptance/restart/Git delivery/new product features.
- Status: **accepted**
- Started: `2026-09-06T01:59:54.579Z`
- Finished: `2026-09-06T02:09:27.400Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `5505e9647da2427aa1035ad3d2ba27df` | 1 | `run_initial_objective` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6a8c566faa1d4d8f8c6433af0148f94e | 5505e9647da2427aa1035ad3d2ba27df | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 077d587c5cd1dcc91d8c6ed940c46404ca30acda15026474dd298aadff3f00f8 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41103 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `6a78d4b1f9c45c582c13ff0e8a620010ea936a2e4e1e2ba7d4de6281b01da2f3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
