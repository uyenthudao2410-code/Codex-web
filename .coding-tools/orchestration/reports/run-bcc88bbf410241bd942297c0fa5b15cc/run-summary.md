# Orchestration Run Summary

- Run: `bcc88bbf410241bd942297c0fa5b15cc`
- Task: `2b0f7588c7f046ea815734ccf156bd4f`
- Objective: Stage A for TG1-TG12: install the one-shot exact writer and workspace patch-artifact adapter from the authoritative handoff, restricted to exactly six paths; preserve ChatWeb GPT-5.6 Sol as controller/final-acceptance owner; do not commit, push, tag, package, publish, release, deploy, reset, restore, clean, rebase, force-release/adopt leases, or manually edit orchestration evidence.
- Status: **accepted**
- Started: `2026-09-01T22:41:46.714Z`
- Finished: `2026-09-01T23:54:46.593Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `2f72661a614a465785cf02ee42360280` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `9c5d85206ea84131aa8484109e08f6ce` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `bee57c5d6cbc4909bf177b23d8053aa4` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 4 | `eb7b1e8f595b4001adb38b33771384c8` | 3 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a548cb100023436b83c418b0a49b58c2 | eb7b1e8f595b4001adb38b33771384c8 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 3763b08a4092b03a012980abc76b7ef2d444fe8c6279ae8f1470934d232f0adc | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 34902 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 34934 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 34984 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 34867 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 34908 | `PROTECTED_PATH_WRITE` | `EXECUTING` |  |
| 34945 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `139`
- Chain head: `74fb7d0f5cb54650850ac2e3920bf89d90829e459c9ab1ed0438fb543f97f627`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
