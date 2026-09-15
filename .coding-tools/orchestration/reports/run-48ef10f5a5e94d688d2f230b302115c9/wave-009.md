# Orchestration Wave 9

- Run: `48ef10f5a5e94d688d2f230b302115c9`
- Wave: `e9cd441e1b724c03baa5e2f261391598`
- Objective: Diagnose and restore the Recovery Supervisor launcher path without touching Recovery Host/runtime or installing packaged mode. Current evidence: development manifest is valid, task action is wscript.exe to the installed VBS, task exits 1, and the stop sentinel disappears after task start while status remains uninstalled. Run three bounded discriminating checks under a stop sentinel: (A) installed supervisor script Action Once, (B) installed VBS launcher via cscript, (C) existing Scheduled Task. Before each check recreate stop.request; after all checks leave stop.request present. Record each exit/result and status. Recovery Host PID/instance must remain unchanged/alive. Do not edit repository source, install/uninstall supervisor/app, reboot/logoff, restart/stop runtime, commit/push/release/deploy.
- Objective revision: `9`
- Objective SHA-256: `c7676c41e9a3cbac90829fe75122261c0105680f41af3ed7bffb847b0ca4e529`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `08882d195b58cd58dfbf4dc38b5773bc312a338a140ba1e57b26f4ed6eb6cc59`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57276 | 2026-09-15T07:04:00.197Z | wave_replanned |  | PREFLIGHT | reason=New read-only evidence after Wave 8 shows stop.request is again absent, status remains uninstalled, task LastTaskResult remains 1, task action is the expected wscript/VBS path, and Recovery Host remains unchanged. The isolated supervisor Once probe had already proven core health. Strategy changes from blind restore to a three-layer discriminating launcher test so we can identify whether the failure is installed PowerShell script, VBS launcher, or Task Scheduler context; each test is bounded and uses stop.request to prevent host spawning. |
| 57277 | 2026-09-15T07:04:00.620Z | observation_span_recorded |  |  |  |
| 57278 | 2026-09-15T07:04:01.230Z | observation_span_recorded |  |  |  |
| 57279 | 2026-09-15T07:04:01.446Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57280 | 2026-09-15T07:04:01.663Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 57281 | 2026-09-15T07:04:01.865Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57282 | 2026-09-15T07:04:02.064Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57283 | 2026-09-15T07:04:02.308Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 57284 | 2026-09-15T07:04:02.556Z | state_transition | READY | ROUTED | reason=route_selected |
| 57285 | 2026-09-15T07:04:02.796Z | observation_span_recorded |  |  |  |
| 57286 | 2026-09-15T07:04:03.398Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a7376314e0c1433cafc7651cc1e6a1ee |
| 57287 | 2026-09-15T07:04:03.607Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57290 | 2026-09-15T07:04:05.126Z | observation_span_recorded |  |  |  |
| 57291 | 2026-09-15T07:04:05.455Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a7376314e0c1433cafc7651cc1e6a1ee |
| 57292 | 2026-09-15T07:04:05.650Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57293 | 2026-09-15T07:04:06.178Z | proof_cache_miss |  |  | reason=cold; stage_id=check:02e5ea79bf288ec0; input_fingerprint=16372d40f22ad32fefe840c957f6d33ef24ffb0de693aafa7d09255a60d7e0c9 |
| 57294 | 2026-09-15T07:04:06.605Z | managed_process_admitted |  |  | owner=default |
| 57295 | 2026-09-15T07:04:06.990Z | managed_process_started |  |  | owner=default |
| 57296 | 2026-09-15T07:04:16.648Z | managed_process_terminal |  |  | owner=default |
| 57297 | 2026-09-15T07:04:17.080Z | proof_recorded |  |  | stage_id=check:02e5ea79bf288ec0; status=passed; cache_hit=False; input_fingerprint=16372d40f22ad32fefe840c957f6d33ef24ffb0de693aafa7d09255a60d7e0c9 |
| 57298 | 2026-09-15T07:04:17.412Z | observation_span_recorded |  |  |  |
| 57299 | 2026-09-15T07:04:17.638Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 57300 | 2026-09-15T07:04:17.863Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 57301 | 2026-09-15T07:04:44.248Z | quality_outcome_recorded |  |  |  |
| 57302 | 2026-09-15T07:04:44.469Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 57303 | 2026-09-15T07:04:44.818Z | observation_span_recorded |  |  |  |
| 57304 | 2026-09-15T07:04:45.128Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 57305 | 2026-09-15T07:04:45.354Z | observation_span_recorded |  |  |  |
| 57306 | 2026-09-15T07:04:45.697Z | observation_span_recorded |  |  |  |
| 57307 | 2026-09-15T07:04:45.908Z | continuity_telemetry_recorded |  |  |  |
| 57308 | 2026-09-15T07:05:27.476Z | continuity_telemetry_recorded |  |  |  |
| 57309 | 2026-09-15T07:05:27.844Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:02e5ea79bf288ec0 | passed | 16372d40f22ad32fefe840c957f6d33ef24ffb0de693aafa7d09255a60d7e0c9 | False | 10541 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 27fe1b2d63a44d07bb735911aa3d21e1 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 0977e017f12455b751f713667ce293c2c782ebfe653b8590ce6979a9d7ccba18 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `199`
- Chain head: `5df739b6b0a8862b1db29dc8a682370cffe395291baedc5598c873c88930372d`
