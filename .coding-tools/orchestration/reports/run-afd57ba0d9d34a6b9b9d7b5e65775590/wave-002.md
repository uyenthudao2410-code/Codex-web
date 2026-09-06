# Orchestration Wave 2

- Run: `afd57ba0d9d34a6b9b9d7b5e65775590`
- Wave: `a154ccaf89ad4fdf968fda1a869b2d63`
- Objective: C5 material current-installer lifecycle after contract checkpoint fd7c90d5d2db477cbc45e7bfa280d3fc and predecessor C4 checkpoint 777480e8957941f9ade53ec06e248d55. Exact HEAD 9e752e34db745cd4fb2d0830a517910eced9c37f. Prove current verified 1.0.0 NSIS clean silent install into C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34\install, launch Recovery Host only with isolated APPDATA/LOCALAPPDATA/user-data and tunnel/autostart disabled, prove descriptor owner/process/path and loopback IPC listener without a network call, kill only that exact isolated process tree, silently uninstall, and verify production descriptor, Recovery Supervisor definition, NSIS registry and pre-existing legacy shortcut are unchanged/clean. Authenticated loopback ping is explicitly not claimed because current server policy denied network permission and permission elicitation is unsupported. No normal UI launch, C4 rerun, source mutation, publish/tag/release/deploy, or forbidden ACK.
- Objective revision: `2`
- Objective SHA-256: `6141ae97554be66c92ee0e91a5f323fcf7c9ec23ab4498c0c0c2d279c73baf16`
- Objective source: `replan_request`
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
| 41571 | 2026-09-06T05:52:11.758Z | wave_replanned |  | PREFLIGHT | reason=NETWORK_PERMISSION_REQUIRED on the first material wave: server safe-mode rejected the authenticated HTTP loopback health probe, and request_permissions returned ELICITATION_UNSUPPORTED. Replan preserves the exact C5 target/HEAD/installer and removes all HTTP/network calls, replacing them with descriptor owner PID, installed executable path and OS listener-table proof. No prior installer step executed in the blocked wave. |
| 41572 | 2026-09-06T05:52:11.926Z | observation_span_recorded |  |  |  |
| 41573 | 2026-09-06T05:52:12.827Z | observation_span_recorded |  |  |  |
| 41574 | 2026-09-06T05:52:13.067Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41575 | 2026-09-06T05:52:13.292Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41576 | 2026-09-06T05:52:13.465Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41577 | 2026-09-06T05:52:13.670Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41578 | 2026-09-06T05:52:13.886Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41579 | 2026-09-06T05:52:14.092Z | state_transition | READY | ROUTED | reason=route_selected |
| 41580 | 2026-09-06T05:52:14.293Z | observation_span_recorded |  |  |  |
| 41581 | 2026-09-06T05:52:15.242Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f223bb7fb4ba4cb39e131c5b902715e3 |
| 41582 | 2026-09-06T05:52:15.467Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41583 | 2026-09-06T05:52:16.333Z | observation_span_recorded |  |  |  |
| 41584 | 2026-09-06T05:52:16.600Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f223bb7fb4ba4cb39e131c5b902715e3 |
| 41585 | 2026-09-06T05:52:16.801Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41586 | 2026-09-06T05:52:17.916Z | proof_cache_miss |  |  | reason=cold; stage_id=check:68b77f6549fec6bd; input_fingerprint=f23eccd71713b7fd02c6e3c13a50fd11a4ddf039624001158dd41fc426e1b5f0 |
| 41587 | 2026-09-06T05:52:18.413Z | managed_process_admitted |  |  | owner=default |
| 41588 | 2026-09-06T05:52:18.738Z | managed_process_started |  |  | owner=default |
| 41589 | 2026-09-06T05:52:19.167Z | managed_process_terminal |  |  | owner=default |
| 41590 | 2026-09-06T05:52:19.535Z | proof_recorded |  |  | stage_id=check:68b77f6549fec6bd; status=failed; cache_hit=False; input_fingerprint=f23eccd71713b7fd02c6e3c13a50fd11a4ddf039624001158dd41fc426e1b5f0 |
| 41591 | 2026-09-06T05:52:19.806Z | observation_span_recorded |  |  |  |
| 41592 | 2026-09-06T05:52:19.976Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 41593 | 2026-09-06T05:52:20.151Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 41594 | 2026-09-06T05:52:20.362Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:68b77f6549fec6bd | failed | f23eccd71713b7fd02c6e3c13a50fd11a4ddf039624001158dd41fc426e1b5f0 | False | 1194 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `114`
- Chain head: `5612743aa5665c91bcb01266569110632f1972baf496a720e10100a01c621dfe`
