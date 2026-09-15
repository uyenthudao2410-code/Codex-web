# Orchestration Run Summary

- Run: `63e32f1dda6b42748b4ef385d92e7a3d`
- Task: `a648d62a654f4d9987a8eb36ba66bed7`
- Objective: C01 installed current-session mode-boundary acceptance with safe restoration. Without modifying source, replace the live same-user Recovery Supervisor from the exact healthy development manifest to the fresh exact packaged `dist/win-unpacked` executable using the supported `-Action Install -Packaged -Executable ... -AppRoot ...` path; prove task/manifest/hash/principal/action identity; terminate only the exact currently authenticated development Recovery Host PID after revalidation; require the installed supervisor to resurrect a fresh packaged Recovery Host with a new PID/instance, runtime_mode=packaged, exact fresh executable/argv, and fresh healthy heartbeat. Then restore the supported development supervisor from the same exact source, terminate only the exact packaged Recovery Host PID after revalidation, and require a fresh development Recovery Host with new PID/instance, exact development executable/workspace argv, and fresh healthy heartbeat. No direct network call from the sandbox, no source mutation, no Coding MCP/Tunnel kill, no publish/commit/push/release.
- Status: **accepted**
- Started: `2026-09-15T08:19:11.208Z`
- Finished: `2026-09-15T08:24:40.731Z`

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
| 1 | `82763d01f6784c29acf20ffa68ebcac1` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `bc8112132a374797a6a5e6843b92a4d5` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `a4f74c547aee4bcbb5385a155da6f42a` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 73b49e808df342e5a346ad0ab827f7ef | a4f74c547aee4bcbb5385a155da6f42a | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | b4c610559cdd4eed02555f48342f37c0fefbf1b1402604d4860a323efc310596 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 58409 | `deterministic` | `deterministic` | explicit_request |
| 58435 | `deterministic` | `deterministic` | explicit_request |
| 58461 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 58424 | `CHECK_FAILED` | `PROVING` |  |
| 58450 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `99`
- Chain head: `39eecb8760c847d63e860be6893d30b2713f1b5a77ce4c0585c9857b9494a4ca`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
