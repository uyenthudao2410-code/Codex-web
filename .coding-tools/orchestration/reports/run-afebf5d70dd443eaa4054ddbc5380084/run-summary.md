# Orchestration Run Summary

- Run: `afebf5d70dd443eaa4054ddbc5380084`
- Task: `d291cb0fd8f84741a9ef13be7b94a061`
- Objective: Implement Execution Hub backend state primitives only: durable Hub client registry, monotonic per-client event cursors, separate controller lease with monotonic fencing token/TTL, operator transfer only to an online registered client, and focused persistence/contention/expiry tests. Do not modify server public schemas, panel, proxy, routing, or existing P1.5 behavior in this wave.
- Status: **accepted**
- Started: `2026-08-14T05:04:46.351Z`
- Finished: `2026-08-14T05:06:26.047Z`

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
| 1 | `7180d92737da41ff995b96f077748c32` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 2 | `8f5ac3c78a704d9ab0aa4817124166ff` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 3 | `52711cc2dee449d78106c61ab2141c8d` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 73d2248e96a240a88032e30d43a76f50 | 52711cc2dee449d78106c61ab2141c8d | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | f49ad9896c1556c734354de2d9e27bec9994950a567babb5fad89895b8e332d4 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 909 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 922 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 932 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 917 | `SOL_REJECTED` | `ACCEPTING` | Critical review: new hub_client_cursors/controller_leases must be referentially bound to real orchestration runs (and cursor/client identity where appropriate). Current green implementation permits orphan controller/cursor rows for nonexistent run ids. Add FK/validation and prove invalid references fail before acceptance. |
| 926 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `fc53484f19e8f2b0276989e9ea53f7dad57aa6af35543dd9f5301b8cb447d5c8`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
