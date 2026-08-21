# Orchestration Wave 1

- Run: `4294a5325b23491683f682a4349dfcf4`
- Wave: `59d86ab9def642ef868480162a322472`
- Objective: Run the remaining P1.1 exact-fingerprint RC source/security gates on the same accepted source baseline: Recovery host-process E2E, OpenCode Flash preflight only with no provider dispatch/cost, and production dependency audit. No mutations, no packaging yet, no commit/push/restart/deploy/release/tag/publish, preserve resident codex-app-server and all .coding-tools evidence.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `cae7694780453fd0ca2fa28930eb916ba245fa23e09666d2e3452811354e9050`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25822 | 2026-08-21T04:17:20.184Z | run_started |  | PREFLIGHT |  |
| 25823 | 2026-08-21T04:17:20.457Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25824 | 2026-08-21T04:17:20.614Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25825 | 2026-08-21T04:17:20.833Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 25826 | 2026-08-21T04:17:21.017Z | state_transition | READY | ROUTED | reason=route_selected |
| 25827 | 2026-08-21T04:17:21.517Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0cb3652db1b341e0883779d75a076dac |
| 25828 | 2026-08-21T04:17:21.699Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25829 | 2026-08-21T04:17:22.184Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0cb3652db1b341e0883779d75a076dac |
| 25830 | 2026-08-21T04:17:22.356Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 25831 | 2026-08-21T04:17:22.743Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:ea9535a6d4fc623b; input_fingerprint=f4715cd87b5200e2780a206d4f0ae5031ecfadcb6d09145eb67c271787cc0c1b |
| 25832 | 2026-08-21T04:17:23.100Z | managed_process_admitted |  |  | owner=default |
| 25833 | 2026-08-21T04:17:23.456Z | managed_process_started |  |  | owner=default |
| 25834 | 2026-08-21T04:17:30.855Z | managed_process_terminal |  |  | owner=default |
| 25835 | 2026-08-21T04:17:31.213Z | proof_recorded |  |  | stage_id=check:ea9535a6d4fc623b; status=passed; cache_hit=False; input_fingerprint=f4715cd87b5200e2780a206d4f0ae5031ecfadcb6d09145eb67c271787cc0c1b |
| 25836 | 2026-08-21T04:17:31.382Z | proof_cache_miss |  |  | reason=cold; stage_id=check:570558c492775bd6; input_fingerprint=2cbd00a3aa2996f94955d355269bbb163f4c0fb273ef78f0398df4750fac122a |
| 25837 | 2026-08-21T04:17:31.739Z | managed_process_admitted |  |  | owner=default |
| 25838 | 2026-08-21T04:17:32.003Z | managed_process_started |  |  | owner=default |
| 25839 | 2026-08-21T04:17:37.880Z | managed_process_terminal |  |  | owner=default |
| 25840 | 2026-08-21T04:17:38.282Z | proof_recorded |  |  | stage_id=check:570558c492775bd6; status=failed; cache_hit=False; input_fingerprint=2cbd00a3aa2996f94955d355269bbb163f4c0fb273ef78f0398df4750fac122a |
| 25841 | 2026-08-21T04:17:38.464Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 25842 | 2026-08-21T04:17:38.627Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 25843 | 2026-08-21T04:17:38.849Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ea9535a6d4fc623b | passed | f4715cd87b5200e2780a206d4f0ae5031ecfadcb6d09145eb67c271787cc0c1b | False | 8160 | 0 |
| check:570558c492775bd6 | failed | 2cbd00a3aa2996f94955d355269bbb163f4c0fb273ef78f0398df4750fac122a | False | 6498 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `b938c363455bac996ccd8a921671a30162b8ca6c241f88704ce4c77145388b9b`
