# Orchestration Wave 1

- Run: `e57f96b081e04e8182361c40ffab5d95`
- Wave: `694b30cc6aeb4162b0a3dc5c56972285`
- Objective: C5 isolated Windows installer lifecycle only. Continue the same user goal after canonical C4 checkpoint 777480e8957941f9ade53ec06e248d55 on exact current main/origin HEAD 9e752e34db745cd4fb2d0830a517910eced9c37f. Do not rerun C4 build/smoke/refresh. Frozen C5 root C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34; install root C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34\install; all test APPDATA/LOCALAPPDATA/user-data stay beneath that root. Historical prior source, if used, is exact commit 026f79b3ab5997cb15f38a3b41769da6a79d790b in external worktree C:\Users\Admin\AppData\Local\Temp\codex-web-c5-prior-026f79b3. Preserve source bytes, all .coding-tools evidence and unrelated work. Never touch the real installed app/profile, Windows login/startup registration, Recovery Supervisor task, or production descriptor except read-only before/after identity snapshots. No publish/tag/release/deploy. Never ACK the forbidden completion report. Acceptance: truthful clean silent 1.0.0 install/uninstall with exact current artifact; isolated recovery-host health with no tunnel/updater/autostart effects; upgrade only if a real reproducible 0.3.4 installer is built from the historical commit; rollback only if actually restored to 0.3.4; final cleanup plus exact production descriptor/install-registry/scheduled-task invariants; terminal C5 checkpoint with exact artifacts/jobs/hashes/roots and proof classification.
- Objective revision: `1`
- Objective SHA-256: `3fa1fa6fcbde5c22c790908e1c9a09beb264d4fd3ff9bd9b4e54b1179970a85b`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: `4d349d411b8887238ad4a1f9f43404a9bef00c6de368373ca6d72f1c271aea86`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41493 | 2026-09-06T05:47:57.870Z | run_started |  | PREFLIGHT |  |
| 41494 | 2026-09-06T05:47:58.445Z | observation_span_recorded |  |  |  |
| 41495 | 2026-09-06T05:47:59.330Z | observation_span_recorded |  |  |  |
| 41496 | 2026-09-06T05:47:59.587Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41497 | 2026-09-06T05:47:59.746Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41498 | 2026-09-06T05:47:59.964Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41499 | 2026-09-06T05:48:00.196Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41500 | 2026-09-06T05:48:00.404Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41501 | 2026-09-06T05:48:00.604Z | state_transition | READY | ROUTED | reason=route_selected |
| 41502 | 2026-09-06T05:48:00.774Z | observation_span_recorded |  |  |  |
| 41503 | 2026-09-06T05:48:01.728Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=12f17bef03154beb923b45b5418647ad |
| 41504 | 2026-09-06T05:48:01.946Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41505 | 2026-09-06T05:48:02.807Z | observation_span_recorded |  |  |  |
| 41506 | 2026-09-06T05:48:03.122Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=12f17bef03154beb923b45b5418647ad |
| 41507 | 2026-09-06T05:48:03.292Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41508 | 2026-09-06T05:48:04.280Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8fbf345c88368916; input_fingerprint=55d9131378ff2d509ecdd36ce0cb24e82faf4bc8ba21ed2b5f630381f2750b08 |
| 41509 | 2026-09-06T05:48:04.628Z | managed_process_admitted |  |  | owner=default |
| 41510 | 2026-09-06T05:48:04.955Z | managed_process_started |  |  | owner=default |
| 41511 | 2026-09-06T05:48:05.592Z | managed_process_terminal |  |  | owner=default |
| 41513 | 2026-09-06T05:48:06.102Z | proof_recorded |  |  | stage_id=check:8fbf345c88368916; status=passed; cache_hit=False; input_fingerprint=55d9131378ff2d509ecdd36ce0cb24e82faf4bc8ba21ed2b5f630381f2750b08 |
| 41515 | 2026-09-06T05:48:06.771Z | observation_span_recorded |  |  |  |
| 41516 | 2026-09-06T05:48:06.954Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41519 | 2026-09-06T05:48:18.063Z | quality_outcome_recorded |  |  |  |
| 41520 | 2026-09-06T05:48:18.278Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 41521 | 2026-09-06T05:48:18.556Z | observation_span_recorded |  |  |  |
| 41522 | 2026-09-06T05:48:18.720Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8fbf345c88368916 | passed | 55d9131378ff2d509ecdd36ce0cb24e82faf4bc8ba21ed2b5f630381f2750b08 | False | 1316 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fd7c90d5d2db477cbc45e7bfa280d3fc | accepted | 9e752e34db745cd4fb2d0830a517910eced9c37f | ac9c00809d23e83c77be53a9bffb5ec6473e3ac25490a925e4657a7d4ef19b89 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `d04db1c6dc465bfc0b37635f755b1a35ea4b0dfb5f68acd063e6acec729d72b3`
