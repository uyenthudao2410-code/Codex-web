# Orchestration Wave 2

- Run: `4294a5325b23491683f682a4349dfcf4`
- Wave: `77bade90a0f14742a9f03dcb22c174c5`
- Objective: Run the remaining P1.1 exact-fingerprint RC source/security gates on the same accepted source baseline: Recovery host-process E2E, OpenCode Flash preflight only with no provider dispatch/cost, and production dependency audit. No mutations, no packaging yet, no commit/push/restart/deploy/release/tag/publish, preserve resident codex-app-server and all .coding-tools evidence.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `cae7694780453fd0ca2fa28930eb916ba245fa23e09666d2e3452811354e9050`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25844 | 2026-08-21T04:18:06.154Z | wave_replanned |  | PREFLIGHT | reason=Recovery E2E passed, while OpenCode --preflight failed specifically with CONTROL_TIMEOUT before any provider dispatch. Changed evidence requires diagnosing the control-plane dependency rather than retrying the same preflight command. |
| 25845 | 2026-08-21T04:18:07.958Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25846 | 2026-08-21T04:24:01.203Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25847 | 2026-08-21T04:25:07.617Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25848 | 2026-08-21T04:25:07.846Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25849 | 2026-08-21T04:25:08.000Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 25850 | 2026-08-21T04:25:08.176Z | state_transition | READY | ROUTED | reason=route_selected |
| 25851 | 2026-08-21T04:25:08.618Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=183ad8aeb88442319bdc39a905c3fbd4 |
| 25852 | 2026-08-21T04:25:08.818Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25853 | 2026-08-21T04:25:09.333Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=183ad8aeb88442319bdc39a905c3fbd4 |
| 25854 | 2026-08-21T04:25:09.474Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 25855 | 2026-08-21T04:25:09.844Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b2bfd4d3113b3f8b; input_fingerprint=339697430be657816f1a9122e0955f998233cd22568b3c266233b1764b980a11 |
| 25856 | 2026-08-21T04:25:10.239Z | managed_process_admitted |  |  | owner=default |
| 25857 | 2026-08-21T04:25:10.571Z | managed_process_started |  |  | owner=default |
| 25858 | 2026-08-21T04:25:12.788Z | managed_process_terminal |  |  | owner=default |
| 25859 | 2026-08-21T04:25:13.106Z | proof_recorded |  |  | stage_id=check:b2bfd4d3113b3f8b; status=passed; cache_hit=False; input_fingerprint=339697430be657816f1a9122e0955f998233cd22568b3c266233b1764b980a11 |
| 25860 | 2026-08-21T04:25:13.310Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 25861 | 2026-08-21T04:25:23.118Z | quality_outcome_recorded |  |  |  |
| 25862 | 2026-08-21T04:25:23.274Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 25863 | 2026-08-21T04:25:23.656Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b2bfd4d3113b3f8b | passed | 339697430be657816f1a9122e0955f998233cd22568b3c266233b1764b980a11 | False | 2937 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 4985a252f36e424884da7732590253b9 | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 80dc849961f359274da04319623df6213f39408f34aca09b9647ad48b8f3d607 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `b938c363455bac996ccd8a921671a30162b8ca6c241f88704ce4c77145388b9b`
