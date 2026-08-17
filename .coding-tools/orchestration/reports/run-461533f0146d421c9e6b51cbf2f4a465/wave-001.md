# Orchestration Wave 1

- Run: `461533f0146d421c9e6b51cbf2f4a465`
- Wave: `1e23e391221140ea95faab14c9692442`
- Objective: Read-only current-HEAD verification of the server-first compute placement contract. Run only the focused webcodex-core compute_placement tests; do not modify files, do not build release artifacts, and do not change runtime configuration.
- Mode: `mcp_only`
- Base HEAD: `3059b218989fda8ebf217d121cd6e8f74a71587d`
- Worktree fingerprint: `d505ffb026c815ff3d03dfcb230d7904c51aab5383ace805b69981c6bb3f8c74`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12100 | 2026-08-17T07:38:04.230Z | run_started |  | PREFLIGHT |  |
| 12101 | 2026-08-17T07:38:04.719Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12102 | 2026-08-17T07:38:04.917Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12103 | 2026-08-17T07:38:05.136Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12104 | 2026-08-17T07:38:05.321Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12105 | 2026-08-17T07:38:05.479Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12106 | 2026-08-17T07:38:05.619Z | state_transition | READY | ROUTED | reason=route_selected |
| 12107 | 2026-08-17T07:38:06.212Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=dd0029d94641447eb16e06f3184eb7b6 |
| 12108 | 2026-08-17T07:38:06.378Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12109 | 2026-08-17T07:38:06.936Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=dd0029d94641447eb16e06f3184eb7b6 |
| 12110 | 2026-08-17T07:38:07.105Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12111 | 2026-08-17T07:38:07.578Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:67144c3fff08377b; input_fingerprint=602bc3ccea1a71740e71dd84c027f02dfefbd04b4fee6149dd2f6c104c6b2b85 |
| 12112 | 2026-08-17T07:38:08.002Z | managed_process_admitted |  |  | owner=default |
| 12113 | 2026-08-17T07:38:08.293Z | managed_process_started |  |  | owner=default |
| 12114 | 2026-08-17T07:38:23.042Z | managed_process_terminal |  |  | owner=default |
| 12115 | 2026-08-17T07:38:23.385Z | proof_recorded |  |  | stage_id=check:67144c3fff08377b; status=passed; cache_hit=False; input_fingerprint=602bc3ccea1a71740e71dd84c027f02dfefbd04b4fee6149dd2f6c104c6b2b85 |
| 12116 | 2026-08-17T07:38:23.622Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12117 | 2026-08-17T07:38:32.343Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12118 | 2026-08-17T07:38:32.738Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:67144c3fff08377b | passed | 602bc3ccea1a71740e71dd84c027f02dfefbd04b4fee6149dd2f6c104c6b2b85 | False | 15509 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 37ef35536738450fa4ff8b49aa2fe2c6 | accepted | 3059b218989fda8ebf217d121cd6e8f74a71587d | 39c678331f5063e48c3e73d4dbe3586d160ff9ff49c21c2be88eed9223c1238e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `e03510a120e5b62d9aab4b4e74bd2ce715500b288f217eeea7ff334a1adf7e4e`
