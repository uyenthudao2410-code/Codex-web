# Orchestration Run Summary

- Run: `b79b05760db84f04b6e4031e83b19fbc`
- Task: `bfe291389a2f45d98d5dacd432ad430d`
- Objective: Correct Codex-web observability so it distinguishes MCP tools/list discovery from the per-invocation token counts shown on Coding-VP Live Tool call cards. The canonical per-tool-call metric must consume an exact invocation/tool-call token receipt from the ChatWeb/Coding-VP client/transport when such metadata is actually exposed; provider/controller model-usage receipts stay separate. Never derive per-tool-call tokens from tools/list, serialized byte size, elapsed time, or aggregate analytics, and never convert missing measurement to zero. Preserve the exact 8-tool smart-v3 contract and bounded non-mutating fast Overview path. Add focused regression coverage and provenance. User screenshot shows card-level counts such as agent_workflow 64,143 tokens and exec_command 895 tokens; determine whether current request metadata, host observation, performance events, or durable tool-call events already carry that exact card count; if not, identify the smallest authoritative ingress needed rather than fabricate it.
- Status: **aborted**
- Started: `2026-08-30T15:22:06.274Z`
- Finished: `2026-08-31T13:58:02.035Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a0ea656f23eb4d74bbbfe092c5a73cc6` | 1 | `run_initial_objective` | `mcp_only` | `9b766f241432b9b5bfa8aa75ae2f1816709a2c2d` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `7`
- Chain head: `ad00ecce5c505436cd009c3c25355fa683e833a110b4a184bfb7ec2d365acf4e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
