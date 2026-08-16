# Orchestration Run Summary

- Run: `00277611ed96493596d2ffc3fa2327de`
- Task: `f2415664a7bf4c7fb3dbecc9750f707f`
- Objective: Fix the demonstrated P3 native semantic timeout contract without changing public smart-v3 tool count. The Python native LSP HTTP client currently times out at 5 seconds while the Rust ToolRuntime permits one agent LSP request to wait 30+2 seconds, and the Connector semantic route processes up to 8 queries. Make the smallest coherent fix: fan out the bounded semantic query ToolRuntime calls concurrently while preserving result order, raise the Python loopback HTTP timeout just above the single-query ToolRuntime wait budget, and add focused regression assertions proving both behaviors. Preserve authentication, workspace binding, fail-closed behavior, redaction, and read-only semantics.
- Status: **accepted**
- Started: `2026-08-15T23:28:13.111Z`
- Finished: `2026-08-16T00:50:10.039Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `fbc291ee553d4fdca5f60935e8824f43` | `mcp_only` | `64ac538ae374965bf8d51428f4b4508363b79f2f` | replanned |
| 2 | `fa17c53bb94c4788ae21af2d0ebd0f45` | `mcp_only` | `64ac538ae374965bf8d51428f4b4508363b79f2f` | replanned |
| 3 | `10b3fb1a6cdd40efa68429025d22083d` | `mcp_only` | `64ac538ae374965bf8d51428f4b4508363b79f2f` | replanned |
| 4 | `0a3718a58482411c955aa9936e2f76cc` | `mcp_only` | `64ac538ae374965bf8d51428f4b4508363b79f2f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a36b7e43e1e144cb97595761e07b97e9 | 0a3718a58482411c955aa9936e2f76cc | accepted | 64ac538ae374965bf8d51428f4b4508363b79f2f | 01b8347685ea297c81adb7047e97ace6363e87bf1f64d1d3d21423ad0cdc0e82 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5526 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 5538 | `deterministic` | `deterministic` | explicit_request |
| 5551 | `deterministic` | `deterministic` | explicit_request |
| 5564 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 5533 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 5546 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 5559 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `52`
- Chain head: `c1d6870c8ced9d1ca41edfc2f4a49ca030d29b126ba0a9a8a0fd6e3ea818ba10`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
