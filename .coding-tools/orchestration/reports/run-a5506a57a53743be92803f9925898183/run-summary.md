# Orchestration Run Summary

- Run: `a5506a57a53743be92803f9925898183`
- Task: `7f38265f7382439aab96f4844b2ada78`
- Objective: Map the P0.3 F1-F9 Recovery fault matrix on exact delivered HEAD 885260b404c2c64df1b1afa835963045ac55dbf6 before any new mutation. For each F1-F9 in docs/PRODUCTION_CLOSURE_ROLLOUT.md, identify exact existing test names/functions/scripts and whether they are deterministic/unit, current-process integration, or isolated packaged real-process evidence. Reuse exact current coverage where it already proves the required behavior. Identify the smallest genuine gaps only. Pay special attention to whether F2 Recovery Host crash + installed Supervisor restart is covered in a real installed/isolated process harness, and whether F3-F6 subordinate owned-process exits are covered with new PID, preserved unaffected peer, exact port/device identity and no duplicate listener. F7/F8/F9 may be deterministic if they fully prove ownership/backoff invariants. Never propose killing the active development Coding MCP/Recovery Host/Tunnels. Return a concrete matrix with exact commands to run and minimal files to change only if needed.
- Status: **accepted**
- Started: `2026-08-17T09:09:05.050Z`
- Finished: `2026-08-17T09:31:02.438Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `e4e3b8b4e914422e8cc4f9141d7290f3` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 2 | `10e0b826c09f4d89acc322395072d9e2` | `deep_single_lane` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 3 | `4637bfc074ad4be6b11ef6eaf49825e1` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 5efd555cbd3b4d3687b91f3097ba466d | 4637bfc074ad4be6b11ef6eaf49825e1 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | bae592655d85cc95d332c5acea13a089ac17fcd23ea02d64cf81b322008bece5 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13160 | `auto` | `deterministic` | roi_gate_hold_insufficient_paired_evidence |
| 13183 | `terra` | `terra` | explicit_request |
| 13198 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13175 | `SOL_REJECTED` | `ACCEPTING` | The verification passed on the unchanged baseline, but no application source files were modified (modified_files/files_modified = 0). The requested Operator Control Panel redesign was therefore not implemented and must be replanned with an implementation-capable route. |
| 13189 | `PROMPT_TOO_LARGE` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `80`
- Chain head: `05b19844e5ace548d94c537611d1f18768f4cbb6596c4721e8b617683fff351d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
