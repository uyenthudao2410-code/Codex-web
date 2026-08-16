# Orchestration Wave 2

- Run: `66b7b687a51046d6a05ca3c521dfa782`
- Wave: `06ee0c6bf71f4d2db6d472ccd450a90a`
- Objective: Replan Phase 3B after 37/38 focused tests passed but the standalone Recovery MCP test parsed an unexpected HTML response on the dynamically allocated port. Strengthen only the process oracle first: capture the spawned Recovery MCP stderr, require the child PID to still be alive after TCP readiness, GET /healthz from the same port and assert service='recovery-mcp' and pid==child.pid before making authenticated MCP requests. Make the generic HTTP helper preserve raw non-JSON bodies in assertion errors instead of throwing JSON.parse. Do not weaken Recovery MCP production behavior or auth assertions. Rerun py_compile and focused recovery-plane test.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `cd88247730fd61cb7ea73e819860ed8e41fb06ad44659e4e00545ba06fdf798f`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6508 | 2026-08-16T08:56:02.170Z | wave_replanned |  | PREFLIGHT | reason=Exact healthz/PID oracle proved the responder is the Recovery MCP. Failure text showed BaseHTTPRequestHandler parsed the unread unauthorized JSON body plus the next POST as an HTTP method, because early 401 returned without consuming body on a persistent connection. Close early-rejected connections instead of weakening auth or changing the test client. |
| 6509 | 2026-08-16T08:56:02.598Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6510 | 2026-08-16T08:56:02.894Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6511 | 2026-08-16T08:56:03.405Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6513 | 2026-08-16T08:56:03.691Z | state_transition | READY | ROUTED | reason=route_selected |
| 6514 | 2026-08-16T08:56:04.870Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ef9f77f3d6a84181bc30de961bd1cb2b |
| 6515 | 2026-08-16T08:56:05.128Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6516 | 2026-08-16T08:56:07.109Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ef9f77f3d6a84181bc30de961bd1cb2b |
| 6517 | 2026-08-16T08:56:07.445Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6518 | 2026-08-16T08:56:08.209Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:25606f562d597b39; input_fingerprint=55e771630ea29fa7c1f8b808ecec15859db4149bd8ce20e499867495b363c170 |
| 6519 | 2026-08-16T08:56:09.008Z | managed_process_admitted |  |  | owner=default |
| 6520 | 2026-08-16T08:56:09.803Z | managed_process_started |  |  | owner=default |
| 6521 | 2026-08-16T08:56:10.604Z | managed_process_terminal |  |  | owner=default |
| 6522 | 2026-08-16T08:56:11.451Z | proof_recorded |  |  | stage_id=check:25606f562d597b39; status=passed; cache_hit=False; input_fingerprint=55e771630ea29fa7c1f8b808ecec15859db4149bd8ce20e499867495b363c170 |
| 6523 | 2026-08-16T08:56:11.792Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9f3f83d6b46d2388; input_fingerprint=49c8fa12884587cb3844fee4361d9c7942d42474b4b7a87eadf3fda1b0ce75b9 |
| 6524 | 2026-08-16T08:56:12.720Z | managed_process_admitted |  |  | owner=default |
| 6525 | 2026-08-16T08:56:13.402Z | managed_process_started |  |  | owner=default |
| 6526 | 2026-08-16T08:56:15.651Z | managed_process_terminal |  |  | owner=default |
| 6527 | 2026-08-16T08:56:16.746Z | proof_recorded |  |  | stage_id=check:9f3f83d6b46d2388; status=passed; cache_hit=False; input_fingerprint=49c8fa12884587cb3844fee4361d9c7942d42474b4b7a87eadf3fda1b0ce75b9 |
| 6528 | 2026-08-16T08:56:17.204Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8d444d33922441a9; input_fingerprint=287dc260b1c0180027ea55de0fcb2a4e74024ad7434f5eb307975fad7391b87c |
| 6529 | 2026-08-16T08:56:18.203Z | managed_process_admitted |  |  | owner=default |
| 6530 | 2026-08-16T08:56:18.914Z | managed_process_started |  |  | owner=default |
| 6531 | 2026-08-16T08:56:20.200Z | managed_process_terminal |  |  | owner=default |
| 6532 | 2026-08-16T08:56:20.943Z | proof_recorded |  |  | stage_id=check:8d444d33922441a9; status=passed; cache_hit=False; input_fingerprint=287dc260b1c0180027ea55de0fcb2a4e74024ad7434f5eb307975fad7391b87c |
| 6533 | 2026-08-16T08:56:21.383Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:328e123c63857fd8; input_fingerprint=07065fa01b3937a2ef0055f4d91c2e65beba9192db98a93c11deafa030a41be2 |
| 6534 | 2026-08-16T08:56:22.148Z | managed_process_admitted |  |  | owner=default |
| 6535 | 2026-08-16T08:56:22.914Z | managed_process_started |  |  | owner=default |
| 6536 | 2026-08-16T08:56:36.493Z | managed_process_terminal |  |  | owner=default |
| 6537 | 2026-08-16T08:56:36.951Z | proof_recorded |  |  | stage_id=check:328e123c63857fd8; status=failed; cache_hit=False; input_fingerprint=07065fa01b3937a2ef0055f4d91c2e65beba9192db98a93c11deafa030a41be2 |
| 6538 | 2026-08-16T08:56:37.210Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 6539 | 2026-08-16T08:56:37.494Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 6540 | 2026-08-16T08:56:38.056Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:25606f562d597b39 | passed | 55e771630ea29fa7c1f8b808ecec15859db4149bd8ce20e499867495b363c170 | False | 2586 | 0 |
| check:9f3f83d6b46d2388 | passed | 49c8fa12884587cb3844fee4361d9c7942d42474b4b7a87eadf3fda1b0ce75b9 | False | 4012 | 0 |
| check:8d444d33922441a9 | passed | 287dc260b1c0180027ea55de0fcb2a4e74024ad7434f5eb307975fad7391b87c | False | 2912 | 0 |
| check:328e123c63857fd8 | failed | 07065fa01b3937a2ef0055f4d91c2e65beba9192db98a93c11deafa030a41be2 | False | 15102 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `271`
- Chain head: `6e3848c269d200d6fca4d0162b782332078ef865e4cd623aea8368f5fef0422d`
