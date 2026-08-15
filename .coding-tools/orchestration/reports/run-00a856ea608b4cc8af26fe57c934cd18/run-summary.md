# Orchestration Run Summary

- Run: `00a856ea608b4cc8af26fe57c934cd18`
- Task: `7c80dffee0f04530a7dbaf160a0223a1`
- Objective: Integrated exact-worktree acceptance proof before live runtime activation. Do not mutate source. Run the full Python MCP regression, root Node/Electron tests, git diff whitespace validation, and conflict check on the current dirty worktree. Do not call providers/reviewers, do not restart inside this proof wave, and preserve all unrelated dirty files.
- Status: **accepted**
- Started: `2026-08-15T05:51:38.925Z`
- Finished: `2026-08-15T05:55:51.880Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `ab62e65f552d418dbd453f47b8411f75` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `8b22231edcfc4e089ba17715e70cfc29` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 3 | `655b9646dd8f44c5a0db16804ed2b63d` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 4 | `92536d71953d42b3ac175ff69407d160` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7c70dc1b1280459683a1b9d021f5849e | 92536d71953d42b3ac175ff69407d160 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 6989f785f45dfd9f8b25fa1314cd1d51d14660340a8d66c0ac0df7cbce3407d5 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4523 | `deterministic` | `deterministic` | explicit_request |
| 4535 | `deterministic` | `deterministic` | explicit_request |
| 4548 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 4560 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4530 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 4543 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 4555 | `INVALID_ARGUMENT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `bc5caa8f4fa786f393f91059ea6faeafddf1bc0de19da96843dea5cc51f0e396`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
