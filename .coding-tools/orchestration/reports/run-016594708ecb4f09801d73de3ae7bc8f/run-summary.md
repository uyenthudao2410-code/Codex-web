# Orchestration Run Summary

- Run: `016594708ecb4f09801d73de3ae7bc8f`
- Task: `fcb26d8379764faca8e9becee0c5bebb`
- Objective: G2-P17 provenance closure ONLY for exact current resources/coding-tools-mcp/coding_tools_mcp/projection_rebuild.py SHA-256 1f51f0213439a6eeac356836f4ac4756565ee044122b1e3c7c36de9e1b48f442; resources/coding-tools-mcp/coding_tools_mcp/runtime_stateless_context.py SHA-256 a01fb14ad86e165c2a7b48ae5f2c7607dc41069bf4936443d072a50fa9343c1b; resources/coding-tools-mcp/coding_tools_mcp/stateless_context.py SHA-256 c46a06ff7808065fea8f370e4ca497a5bb67349f34f033cdb5a65697255e3dc0. Adopt these exact existing files without changing source bytes. Causal objective: recover an exact archived task/RUN context only; refuse any active conflicting task; refuse pending operator report; preserve controller/final-acceptance authority; never fall back to last_active_workspace, UI workspace, most-recent task, or a global active task. Oracle files are read-only and outside acceptance scope. Preserve dirty worktree and all .coding-tools evidence. No direct SQLite; do not reconcile stale RUNs; no bulk/out-of-scope adoption; no reset/restore/clean/rebase; no commit/push/tag/release/publish/deploy; no synthetic Problems/outcomes.
- Status: **accepted**
- Started: `2026-09-03T18:50:01.181Z`
- Finished: `2026-09-03T18:50:38.122Z`

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
| 1 | `30a73e3ddb0c45dbb0144ba2525d800d` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| b7876e3d360340ec9a1d000736a46977 | 30a73e3ddb0c45dbb0144ba2525d800d | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 06701a7ea741cfb19cfd1a055923cd9a5742c3a4ca25454c41bd1452e3488077 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 38683 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `c5e0fc00ffe60812a8c892a32d50ac0b662af8cbbf87721af20515d016fc8427`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
