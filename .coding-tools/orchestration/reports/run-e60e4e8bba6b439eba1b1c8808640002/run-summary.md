# Orchestration Run Summary

- Run: `e60e4e8bba6b439eba1b1c8808640002`
- Task: `ee6d9a082bd849739aecbbeeceb471d5`
- Objective: Create a narrow accepted-code activation-authority checkpoint for the already-committed semantic-provider fix at current HEAD. Do not edit source. Adopt only the exact existing semantic_localization.py and context_tools.py bytes, run bounded semantic-provider regression proof, and accept this auxiliary non-problem wave solely so coding_mcp may be restarted. Do not close or supersede the canonical Problem RUN 80fd4f520875418fbea2205071984d11.
- Status: **aborted**
- Started: `2026-09-12T12:45:26.981Z`
- Finished: `2026-09-15T08:59:42.142Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `69d7d44953f14c5da26e7648cab28ea0` | 1 | `run_initial_objective` | `mcp_only` | `228b91e6128479d4b3699e622d4f51dd431acb24` | replanned |
| 2 | `13dd060b09444341a6d5fbde51d728b3` | 2 | `replan_request` | `mcp_only` | `228b91e6128479d4b3699e622d4f51dd431acb24` | replanned |
| 3 | `debb29ce64fe428191d2f79f1072edd7` | 3 | `replan_request` | `mcp_only` | `228b91e6128479d4b3699e622d4f51dd431acb24` | replanned |
| 4 | `50b2f828ce734cccac6aba1aa4aac0a4` | 4 | `replan_request` | `mcp_only` | `228b91e6128479d4b3699e622d4f51dd431acb24` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51957 | `deterministic` | `deterministic` | explicit_request |
| 51974 | `deterministic` | `deterministic` | explicit_request |
| 51998 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 51963 | `EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED` | `EXECUTING` |  |
| 51988 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 52027 | `SOL_REJECTED` | `ACCEPTING` | Acceptance correctly failed because the passed proof-source binding had an empty path set and therefore did not cover the two exact clean semantic source files. Replan to a no-write dry-run patch against those same files so proof-source binding covers their current bytes; then rerun the focused oracle and attest exact SHA-256 values. No source mutation is authorized or needed. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `86`
- Chain head: `a1e9e62bc135fd80ee11a45cf4424c2e0199556dfe3485dc430eb14b108768c3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
