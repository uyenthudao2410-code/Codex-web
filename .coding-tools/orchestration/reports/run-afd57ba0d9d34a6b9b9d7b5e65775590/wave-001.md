# Orchestration Wave 1

- Run: `afd57ba0d9d34a6b9b9d7b5e65775590`
- Wave: `df4816b01faa45b08abd2e31154a15b6`
- Objective: C5 material lifecycle continuation after C5 contract checkpoint fd7c90d5d2db477cbc45e7bfa280d3fc and predecessor C4 checkpoint 777480e8957941f9ade53ec06e248d55. On exact HEAD 9e752e34db745cd4fb2d0830a517910eced9c37f, prove only the current verified 1.0.0 NSIS clean silent install, isolated recovery-host authenticated health, exact isolated process cleanup, silent uninstall, and production invariants. Use C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34 only. Do not normal-launch the Electron UI because that path calls Windows login-item settings. Do not touch C4 build/smoke/refresh, production profile, Recovery Supervisor, production descriptor except read-only snapshots, or the pre-existing legacy Start Menu shortcut. Preserve all repository source/evidence. No publish/tag/release/deploy; never ACK the forbidden report.
- Objective revision: `1`
- Objective SHA-256: `8254721786492cdced3f94bcef7b0311c4790be49185a45c647d5744f41a1285`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: `4d349d411b8887238ad4a1f9f43404a9bef00c6de368373ca6d72f1c271aea86`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41543 | 2026-09-06T05:50:44.950Z | run_started |  | PREFLIGHT |  |
| 41544 | 2026-09-06T05:50:45.291Z | observation_span_recorded |  |  |  |
| 41545 | 2026-09-06T05:50:46.233Z | observation_span_recorded |  |  |  |
| 41546 | 2026-09-06T05:50:46.427Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41547 | 2026-09-06T05:50:46.669Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41548 | 2026-09-06T05:50:46.858Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41549 | 2026-09-06T05:50:47.124Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41550 | 2026-09-06T05:50:47.325Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41551 | 2026-09-06T05:50:47.484Z | state_transition | READY | ROUTED | reason=route_selected |
| 41552 | 2026-09-06T05:50:47.679Z | observation_span_recorded |  |  |  |
| 41553 | 2026-09-06T05:50:48.625Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a7f81eb334a9498ca3bafcfacf2dd4fa |
| 41554 | 2026-09-06T05:50:48.805Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41555 | 2026-09-06T05:50:49.728Z | observation_span_recorded |  |  |  |
| 41556 | 2026-09-06T05:50:50.032Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a7f81eb334a9498ca3bafcfacf2dd4fa |
| 41557 | 2026-09-06T05:50:50.216Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41558 | 2026-09-06T05:50:51.140Z | proof_cache_miss |  |  | reason=cold; stage_id=check:eca44ccbc6edc732; input_fingerprint=07d6566b002bd890e306240e0149a633439d93f8ec9fe6ff74c6b963dd8d5e3a |
| 41559 | 2026-09-06T05:50:51.393Z | observation_span_recorded |  |  |  |
| 41560 | 2026-09-06T05:50:51.565Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 41561 | 2026-09-06T05:50:51.769Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 41562 | 2026-09-06T05:50:51.987Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `114`
- Chain head: `5612743aa5665c91bcb01266569110632f1972baf496a720e10100a01c621dfe`
