# Orchestration Run Summary

- Run: `31b80d1d320541cf908e586864d43979`
- Task: `6d50797a41cc431ea7506dd67b030c60`
- Objective: Add an OpenCode-only compatibility mode to the existing hub_proxy_stdio so OpenCode models can consume Coding Tools MCP structuredContent. Preserve Codex Desktop default behavior and the 8-tool public contract. Inspect only the proxy, its focused tests, and opencode.json. No writes in prepare.
- Status: **accepted**
- Started: `2026-08-14T06:47:49.156Z`
- Finished: `2026-08-14T06:53:52.987Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `5c3eccab8737482bba7f01bfe304c25f` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 2 | `1b0bbed1448d4ed3a64574c3e8174ef2` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 01687830a5184c90a872a831492aa204 | 1b0bbed1448d4ed3a64574c3e8174ef2 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | d1af3df5865d973541bddce1f723848b2cf75e6adc56367f760c0941a71e2a46 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1432 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1445 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1440 | `SOL_REJECTED` | `ACCEPTING` | Live OpenCode canary failed with MCP -32600 because outputSchema validation requires structuredContent to remain present. Replan compatibility mode to preserve structuredContent for SDK/schema validation while mirroring its JSON into the first text content block for model visibility; keep this opt-in only for OpenCode. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `ef0a68d8c06154f8b26f31494f1d609f9b638b261acd4344b5459037950e22b6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
