# Orchestration Wave 2

- Run: `405ae4561b174ae9b228fdbdf6a172ec`
- Wave: `dff1d4c001e44eca8114948ee7dbb169`
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
| 23807 | 2026-08-20T11:00:05.663Z | wave_replanned |  | PREFLIGHT | reason=The previous wave failed before any source write because cargo fmt --check found a pre-existing formatting diff in crates/webcodex-core/src/source_snapshot.rs, outside W3 scope. The new strategy preserves W3 semantics but uses focused/touched-surface formatting and tests so unrelated baseline formatting drift cannot block the causal patch. |
| 23808 | 2026-08-20T11:00:06.688Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23809 | 2026-08-20T11:00:39.897Z | managed_process_admitted |  |  | owner=default |
| 23810 | 2026-08-20T11:00:40.188Z | managed_process_started |  |  | owner=default |
| 23811 | 2026-08-20T11:00:43.431Z | managed_process_terminal |  |  | owner=default |
| 23812 | 2026-08-20T11:03:35.774Z | managed_process_admitted |  |  | owner=default |
| 23813 | 2026-08-20T11:03:36.163Z | managed_process_started |  |  | owner=default |
| 23814 | 2026-08-20T11:03:36.824Z | managed_process_terminal |  |  | owner=default |
| 23815 | 2026-08-20T11:04:59.683Z | managed_process_admitted |  |  | owner=default |
| 23816 | 2026-08-20T11:04:59.981Z | managed_process_started |  |  | owner=default |
| 23817 | 2026-08-20T11:05:00.507Z | managed_process_terminal |  |  | owner=default |
| 23818 | 2026-08-20T11:06:15.940Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23819 | 2026-08-20T11:06:16.086Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23820 | 2026-08-20T11:06:16.245Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 23821 | 2026-08-20T11:06:16.381Z | state_transition | READY | ROUTED | reason=route_selected |
| 23822 | 2026-08-20T11:06:17.084Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a8ca7b751b254a42ba0d8c3325895d9e |
| 23823 | 2026-08-20T11:06:17.266Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23824 | 2026-08-20T11:06:17.844Z | patch_surface_observed |  |  |  |
| 23825 | 2026-08-20T11:06:18.119Z | patch_surface_observed |  |  |  |
| 23826 | 2026-08-20T11:06:18.321Z | patch_surface_observed |  |  |  |
| 23827 | 2026-08-20T11:06:18.622Z | patch_surface_observed |  |  |  |
| 23828 | 2026-08-20T11:06:18.961Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a8ca7b751b254a42ba0d8c3325895d9e |
| 23829 | 2026-08-20T11:06:19.163Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23830 | 2026-08-20T11:06:19.586Z | proof_cache_miss |  |  | reason=cold; stage_id=check:796009f75ffcdfa8; input_fingerprint=e1a9130e7ede2cc66b6ab8d20d48354553673ce2796b5413079e0579aa85db51 |
| 23831 | 2026-08-20T11:06:19.946Z | managed_process_admitted |  |  | owner=default |
| 23832 | 2026-08-20T11:06:20.346Z | managed_process_started |  |  | owner=default |
| 23833 | 2026-08-20T11:06:23.805Z | managed_process_terminal |  |  | owner=default |
| 23834 | 2026-08-20T11:06:24.163Z | proof_recorded |  |  | stage_id=check:796009f75ffcdfa8; status=failed; cache_hit=False; input_fingerprint=e1a9130e7ede2cc66b6ab8d20d48354553673ce2796b5413079e0579aa85db51 |
| 23835 | 2026-08-20T11:06:24.329Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 23836 | 2026-08-20T11:06:24.544Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 23837 | 2026-08-20T11:06:24.723Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:796009f75ffcdfa8 | failed | e1a9130e7ede2cc66b6ab8d20d48354553673ce2796b5413079e0579aa85db51 | False | 4258 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `92`
- Chain head: `13bd3dcf5b6a43a974630348237ba063adea6d732954e8e57c381afd085470a9`
