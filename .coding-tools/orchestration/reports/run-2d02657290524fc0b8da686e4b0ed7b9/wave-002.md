# Orchestration Wave 2

- Run: `2d02657290524fc0b8da686e4b0ed7b9`
- Wave: `83b682db38b34808bcc71053e5a7a932`
- Objective: Validate and accept the exact completed source for permanent direct Windows host execution without ProcessContainer or Windows Sandbox, preserving permission controls, existing workspace/node identity and unrelated work.
- Objective revision: `1`
- Objective SHA-256: `6600e4dfcbc503504f05e4750077f016ba4dc14a54cb86e1950e65da3387a626`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `5c5e207265f56a69b72f16dd78c4d2951f382609`
- Worktree fingerprint: `6eeba1272308f652a518446ab5c3b32c73df3ac2cee04b63bccc404bc5c64fac`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 61525 | 2026-10-22T07:17:42.150Z | wave_replanned |  | PREFLIGHT | reason=The prior attempt refused BASE_DRIFT before adoption or process spawn. HEAD and all 23 explicitly approved source SHA256 values remain identical; only runtime evidence reports changed. Rebind this new proof wave to the currently observed worktree and execute the exact approved direct-host focused tests. |
| 61526 | 2026-10-22T07:17:42.526Z | observation_span_recorded |  |  |  |
| 61527 | 2026-10-22T07:17:42.850Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 61528 | 2026-10-22T07:17:43.081Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 61529 | 2026-10-22T07:17:43.278Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 61530 | 2026-10-22T07:17:43.476Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 61531 | 2026-10-22T07:17:43.679Z | state_transition | READY | ROUTED | reason=route_selected |
| 61532 | 2026-10-22T07:17:43.901Z | observation_span_recorded |  |  |  |
| 61533 | 2026-10-22T07:17:44.654Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=332e12cac2ea4a429f8b589003a3f98b |
| 61534 | 2026-10-22T07:17:44.955Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 61535 | 2026-10-22T07:17:45.598Z | existing_file_adoption_observed |  |  |  |
| 61536 | 2026-10-22T07:17:45.922Z | observation_span_recorded |  |  |  |
| 61537 | 2026-10-22T07:17:46.286Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=332e12cac2ea4a429f8b589003a3f98b |
| 61538 | 2026-10-22T07:17:46.469Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 61539 | 2026-10-22T07:17:47.086Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fb6fb0468975e705; input_fingerprint=2b686c62dfd62488fe1e3be664f562811ea386d7d516da3cb019ba520858fe35 |
| 61540 | 2026-10-22T07:17:47.602Z | managed_process_admitted |  |  | owner=default |
| 61541 | 2026-10-22T07:17:47.984Z | managed_process_started |  |  | owner=default |
| 61542 | 2026-10-22T07:17:48.802Z | managed_process_terminal |  |  | owner=default |
| 61543 | 2026-10-22T07:17:49.250Z | proof_recorded |  |  | stage_id=check:fb6fb0468975e705; status=passed; cache_hit=False; input_fingerprint=2b686c62dfd62488fe1e3be664f562811ea386d7d516da3cb019ba520858fe35 |
| 61544 | 2026-10-22T07:17:49.533Z | observation_span_recorded |  |  |  |
| 61545 | 2026-10-22T07:17:49.729Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 61546 | 2026-10-22T07:17:50.005Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 61547 | 2026-10-22T07:18:35.512Z | controller_transferred | ACCEPTING | ACCEPTING |  |
| 61548 | 2026-10-22T07:18:38.081Z | quality_outcome_recorded |  |  |  |
| 61549 | 2026-10-22T07:18:38.294Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 61550 | 2026-10-22T07:18:38.623Z | observation_span_recorded |  |  |  |
| 61551 | 2026-10-22T07:18:38.973Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 61552 | 2026-10-22T07:18:39.267Z | observation_span_recorded |  |  |  |
| 61553 | 2026-10-22T07:18:39.653Z | observation_span_recorded |  |  |  |
| 61554 | 2026-10-22T07:18:39.981Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fb6fb0468975e705 | passed | 2b686c62dfd62488fe1e3be664f562811ea386d7d516da3cb019ba520858fe35 | False | 1770 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 43775b875a4a4d84b37aedce671f9d57 | accepted | 5c5e207265f56a69b72f16dd78c4d2951f382609 | d81a8ab72e9217dd4c4de16880a8bf395e91b5e236d653d9c487485872752fb0 | codex-desktop |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `4954f4b413b2cae8e0d13e9f6b688d1dd453d84aa837a78c78fae98f6c70cd7b`
