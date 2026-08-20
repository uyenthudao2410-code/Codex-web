# Orchestration Run Summary

- Run: `405ae4561b174ae9b228fdbdf6a172ec`
- Task: `fda3d2b8dc7a492a8c7efeec5977aeba`
- Objective: S2/W3: implement authenticated caller attribution for durable HTTP/MCP action audit events and make audit-stats coverage explicit, adapted to this repository's current architecture. Required invariants from upstream PRs #82/#83: snapshot non-secret authenticated principal_kind, optional principal_user_id, and OAuth-only oauth_client_id at action-event write time; legacy rows remain NULL and are never inferred/backfilled; agent allowed_client_id must never be misreported as oauth_client_id; ordinary audit-session event responses must not expose these identity fields; audit stats may expose aggregate principal-kind and OAuth-client counts but not stable user IDs; stats must report scanned/available/session/truncation coverage; unknown scoped session returns 404; DB read errors fail instead of silently skipping; count+bounded rows for a session must come from one SQLite read snapshot. Preserve current action-session semantics, auth authority, P4/P5 routing semantics, smart-v3 surface, all unrelated WIP, and .coding-tools evidence. No worktrees, commit, push, restart, deploy, or release.
- Status: **accepted**
- Started: `2026-08-20T10:56:34.587Z`
- Finished: `2026-08-20T11:20:11.345Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `1f12e911a24e4acaab4457925b2e11c4` | `mcp_only` | `66c2d17b68969c3a413b867cc7281f80fbaf4b45` | replanned |
| 2 | `dff1d4c001e44eca8114948ee7dbb169` | `mcp_only` | `66c2d17b68969c3a413b867cc7281f80fbaf4b45` | replanned |
| 3 | `c5ff66f9602e4bfda9982e7d36938bb1` | `mcp_only` | `66c2d17b68969c3a413b867cc7281f80fbaf4b45` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| db605d6998df40aa9afdfbefbe9ad30f | c5ff66f9602e4bfda9982e7d36938bb1 | accepted | 66c2d17b68969c3a413b867cc7281f80fbaf4b45 | ab0c178601135c8f3b1218209190c0b301340a338a840d2576300666cc04ef74 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 23793 | `deterministic` | `deterministic` | explicit_request |
| 23820 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 23841 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 23804 | `CHECK_FAILED` | `PROVING` |  |
| 23835 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `92`
- Chain head: `13bd3dcf5b6a43a974630348237ba063adea6d732954e8e57c381afd085470a9`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
