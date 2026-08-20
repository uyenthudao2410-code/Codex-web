# Orchestration Wave 1

- Run: `405ae4561b174ae9b228fdbdf6a172ec`
- Wave: `1f12e911a24e4acaab4457925b2e11c4`
- Objective: S2/W3: implement authenticated caller attribution for durable HTTP/MCP action audit events and make audit-stats coverage explicit, adapted to this repository's current architecture. Required invariants from upstream PRs #82/#83: snapshot non-secret authenticated principal_kind, optional principal_user_id, and OAuth-only oauth_client_id at action-event write time; legacy rows remain NULL and are never inferred/backfilled; agent allowed_client_id must never be misreported as oauth_client_id; ordinary audit-session event responses must not expose these identity fields; audit stats may expose aggregate principal-kind and OAuth-client counts but not stable user IDs; stats must report scanned/available/session/truncation coverage; unknown scoped session returns 404; DB read errors fail instead of silently skipping; count+bounded rows for a session must come from one SQLite read snapshot. Preserve current action-session semantics, auth authority, P4/P5 routing semantics, smart-v3 surface, all unrelated WIP, and .coding-tools evidence. No worktrees, commit, push, restart, deploy, or release.
- Mode: `mcp_only`
- Base HEAD: `66c2d17b68969c3a413b867cc7281f80fbaf4b45`
- Worktree fingerprint: `62e98f2b814dfe04c1aff6ae20bdf909413449eaf3e00c92de350257f772daa0`
- Contract fingerprint: `0f3549eb151dcddaf4d0ff0ed26f23ad002cd95581333480f46f9279b3942def`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 23788 | 2026-08-20T10:56:34.834Z | run_started |  | PREFLIGHT |  |
| 23789 | 2026-08-20T10:56:35.994Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23790 | 2026-08-20T10:58:19.000Z | solution_shadow_recommended |  |  |  |
| 23791 | 2026-08-20T10:58:31.243Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23792 | 2026-08-20T10:58:31.424Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23793 | 2026-08-20T10:58:31.618Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 23794 | 2026-08-20T10:58:31.759Z | state_transition | READY | ROUTED | reason=route_selected |
| 23795 | 2026-08-20T10:58:32.475Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=18414a154cd64ca28482f71f57ac3586 |
| 23796 | 2026-08-20T10:58:32.656Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23797 | 2026-08-20T10:58:33.200Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=18414a154cd64ca28482f71f57ac3586 |
| 23798 | 2026-08-20T10:58:33.330Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23799 | 2026-08-20T10:58:33.771Z | proof_cache_miss |  |  | reason=cold; stage_id=check:194fabc0129ce4a9; input_fingerprint=ac491d9a55834de836f21f3986f5492d4cd2fc81449684b87cdc33e890ade33b |
| 23800 | 2026-08-20T10:58:34.201Z | managed_process_admitted |  |  | owner=default |
| 23801 | 2026-08-20T10:58:34.511Z | managed_process_started |  |  | owner=default |
| 23802 | 2026-08-20T10:58:40.738Z | managed_process_terminal |  |  | owner=default |
| 23803 | 2026-08-20T10:58:41.075Z | proof_recorded |  |  | stage_id=check:194fabc0129ce4a9; status=failed; cache_hit=False; input_fingerprint=ac491d9a55834de836f21f3986f5492d4cd2fc81449684b87cdc33e890ade33b |
| 23804 | 2026-08-20T10:58:41.255Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 23805 | 2026-08-20T10:58:41.427Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 23806 | 2026-08-20T10:58:41.612Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:194fabc0129ce4a9 | failed | ac491d9a55834de836f21f3986f5492d4cd2fc81449684b87cdc33e890ade33b | False | 6962 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `92`
- Chain head: `13bd3dcf5b6a43a974630348237ba063adea6d732954e8e57c381afd085470a9`
