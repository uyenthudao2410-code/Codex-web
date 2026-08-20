# Orchestration Wave 3

- Run: `405ae4561b174ae9b228fdbdf6a172ec`
- Wave: `c5ff66f9602e4bfda9982e7d36938bb1`
- Objective: S2/W3: implement authenticated caller attribution for durable HTTP/MCP action audit events and make audit-stats coverage explicit, adapted to this repository's current architecture. Required invariants from upstream PRs #82/#83: snapshot non-secret authenticated principal_kind, optional principal_user_id, and OAuth-only oauth_client_id at action-event write time; legacy rows remain NULL and are never inferred/backfilled; agent allowed_client_id must never be misreported as oauth_client_id; ordinary audit-session event responses must not expose these identity fields; audit stats may expose aggregate principal-kind and OAuth-client counts but not stable user IDs; stats must report scanned/available/session/truncation coverage; unknown scoped session returns 404; DB read errors fail instead of silently skipping; count+bounded rows for a session must come from one SQLite read snapshot. Preserve current action-session semantics, auth authority, P4/P5 routing semantics, smart-v3 surface, all unrelated WIP, and .coding-tools evidence. No worktrees, commit, push, restart, deploy, or release.
- Mode: `mcp_only`
- Base HEAD: `66c2d17b68969c3a413b867cc7281f80fbaf4b45`
- Worktree fingerprint: `b4ecaf6bd777a3c3ea24a1768bded6f98f6a333c7e747fa2a86ac5849db87bf3`
- Contract fingerprint: `0f3549eb151dcddaf4d0ff0ed26f23ad002cd95581333480f46f9279b3942def`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 23838 | 2026-08-20T11:06:58.590Z | wave_replanned |  | PREFLIGHT | reason=The W3 source patch is already applied. The prior wave stopped at the first check because rustfmt requested only line wrapping for two new assert_eq statements in src/audit_http/tests.rs. This wave applies exactly that formatter delta, then runs the compile and focused behavior/migration proofs that were not reached previously. |
| 23839 | 2026-08-20T11:06:58.727Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23840 | 2026-08-20T11:06:58.888Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23841 | 2026-08-20T11:06:59.064Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 23842 | 2026-08-20T11:06:59.277Z | state_transition | READY | ROUTED | reason=route_selected |
| 23843 | 2026-08-20T11:06:59.759Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c1e27cbfc92b43a0a7a16c39345f81fc |
| 23844 | 2026-08-20T11:06:59.906Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23845 | 2026-08-20T11:07:00.257Z | patch_surface_observed |  |  |  |
| 23846 | 2026-08-20T11:07:00.518Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c1e27cbfc92b43a0a7a16c39345f81fc |
| 23847 | 2026-08-20T11:07:00.663Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23848 | 2026-08-20T11:07:01.045Z | proof_cache_miss |  |  | reason=cold; stage_id=check:796009f75ffcdfa8; input_fingerprint=4cd5b91dd43a945735d71dda21cda610eb5954f278ec6405cd1d3b36a7f82706 |
| 23849 | 2026-08-20T11:07:01.385Z | managed_process_admitted |  |  | owner=default |
| 23850 | 2026-08-20T11:07:01.747Z | managed_process_started |  |  | owner=default |
| 23851 | 2026-08-20T11:07:04.579Z | managed_process_terminal |  |  | owner=default |
| 23852 | 2026-08-20T11:07:05.014Z | proof_recorded |  |  | stage_id=check:796009f75ffcdfa8; status=passed; cache_hit=False; input_fingerprint=4cd5b91dd43a945735d71dda21cda610eb5954f278ec6405cd1d3b36a7f82706 |
| 23853 | 2026-08-20T11:07:05.265Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a474137ad3527952; input_fingerprint=0e8c99eb0e6278cccc6ee84d28bb7f43581b838409f55ace13bb2385ed9f686e |
| 23854 | 2026-08-20T11:07:05.722Z | managed_process_admitted |  |  | owner=default |
| 23855 | 2026-08-20T11:07:06.033Z | managed_process_started |  |  | owner=default |
| 23856 | 2026-08-20T11:08:47.642Z | managed_process_terminal |  |  | owner=default |
| 23857 | 2026-08-20T11:08:48.055Z | proof_recorded |  |  | stage_id=check:a474137ad3527952; status=passed; cache_hit=False; input_fingerprint=0e8c99eb0e6278cccc6ee84d28bb7f43581b838409f55ace13bb2385ed9f686e |
| 23858 | 2026-08-20T11:08:48.255Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2d9c1dfbde51e17e; input_fingerprint=703fb9b950e76cd70c11e952c378de40a369ae1140439f95a0e9a0d1b7764a46 |
| 23859 | 2026-08-20T11:08:48.626Z | managed_process_admitted |  |  | owner=default |
| 23860 | 2026-08-20T11:08:49.290Z | managed_process_started |  |  | owner=default |
| 23861 | 2026-08-20T11:13:05.704Z | managed_process_terminal |  |  | owner=default |
| 23862 | 2026-08-20T11:13:06.525Z | proof_recorded |  |  | stage_id=check:2d9c1dfbde51e17e; status=passed; cache_hit=False; input_fingerprint=703fb9b950e76cd70c11e952c378de40a369ae1140439f95a0e9a0d1b7764a46 |
| 23863 | 2026-08-20T11:13:06.898Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b4c531703b57fc76; input_fingerprint=a9da1774ab7df35a546498f5b417672c43c6d9740c2a1d4308d9889cb0c63b34 |
| 23864 | 2026-08-20T11:13:07.707Z | managed_process_admitted |  |  | owner=default |
| 23865 | 2026-08-20T11:13:08.116Z | managed_process_started |  |  | owner=default |
| 23866 | 2026-08-20T11:13:09.164Z | managed_process_terminal |  |  | owner=default |
| 23867 | 2026-08-20T11:13:09.602Z | proof_recorded |  |  | stage_id=check:b4c531703b57fc76; status=passed; cache_hit=False; input_fingerprint=a9da1774ab7df35a546498f5b417672c43c6d9740c2a1d4308d9889cb0c63b34 |
| 23868 | 2026-08-20T11:13:09.797Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8295de0502311765; input_fingerprint=412464011d6f95eca424a420095e88f0812707b9c77e6815550ea179f2c48936 |
| 23869 | 2026-08-20T11:13:10.211Z | managed_process_admitted |  |  | owner=default |
| 23870 | 2026-08-20T11:13:10.574Z | managed_process_started |  |  | owner=default |
| 23871 | 2026-08-20T11:13:11.448Z | managed_process_terminal |  |  | owner=default |
| 23872 | 2026-08-20T11:13:11.864Z | proof_recorded |  |  | stage_id=check:8295de0502311765; status=passed; cache_hit=False; input_fingerprint=412464011d6f95eca424a420095e88f0812707b9c77e6815550ea179f2c48936 |
| 23873 | 2026-08-20T11:13:12.466Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 23874 | 2026-08-20T11:19:57.063Z | managed_process_admitted |  |  | owner=default |
| 23875 | 2026-08-20T11:19:57.396Z | managed_process_started |  |  | owner=default |
| 23876 | 2026-08-20T11:19:57.922Z | managed_process_terminal |  |  | owner=default |
| 23877 | 2026-08-20T11:20:10.890Z | quality_outcome_recorded |  |  |  |
| 23878 | 2026-08-20T11:20:11.094Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 23879 | 2026-08-20T11:20:11.420Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:796009f75ffcdfa8 | passed | 4cd5b91dd43a945735d71dda21cda610eb5954f278ec6405cd1d3b36a7f82706 | False | 3631 | 0 |
| check:a474137ad3527952 | passed | 0e8c99eb0e6278cccc6ee84d28bb7f43581b838409f55ace13bb2385ed9f686e | False | 102441 | 0 |
| check:2d9c1dfbde51e17e | passed | 703fb9b950e76cd70c11e952c378de40a369ae1140439f95a0e9a0d1b7764a46 | False | 257715 | 0 |
| check:b4c531703b57fc76 | passed | a9da1774ab7df35a546498f5b417672c43c6d9740c2a1d4308d9889cb0c63b34 | False | 2005 | 0 |
| check:8295de0502311765 | passed | 412464011d6f95eca424a420095e88f0812707b9c77e6815550ea179f2c48936 | False | 1724 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| db605d6998df40aa9afdfbefbe9ad30f | accepted | 66c2d17b68969c3a413b867cc7281f80fbaf4b45 | ab0c178601135c8f3b1218209190c0b301340a338a840d2576300666cc04ef74 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `92`
- Chain head: `13bd3dcf5b6a43a974630348237ba063adea6d732954e8e57c381afd085470a9`
