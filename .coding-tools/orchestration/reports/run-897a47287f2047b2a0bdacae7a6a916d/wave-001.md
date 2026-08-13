# Orchestration Wave 1

- Run: `897a47287f2047b2a0bdacae7a6a916d`
- Wave: `b52dcf051c86468fb1873fb35ff37a4c`
- Objective: Implement Wave C backward-compatible command handle cleanup: command_id becomes the preferred model-facing command handle/output-ref prefix, while deprecated session_id and session:<id>:... remain accepted. Keep internal durable Codex/provider sessions unchanged, keep exactly 8 smart tools, and preserve Wave A/B/D behavior. Do not commit or push.
- Mode: `mcp_only`
- Base HEAD: `a051897449827e4753b16def1b693d867fad76e9`
- Worktree fingerprint: `58127fc0196252b04353899738c17bcd74a2e85a59b426e6eb1a7b5fe97a272f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 354 | 2026-08-13T09:25:35.736Z | run_started |  | PREFLIGHT |  |
| 355 | 2026-08-13T09:25:36.061Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 356 | 2026-08-13T09:25:36.254Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 357 | 2026-08-13T09:25:36.455Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 358 | 2026-08-13T09:25:36.651Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 359 | 2026-08-13T09:25:36.930Z | state_transition | READY | ROUTED | reason=route_selected |
| 360 | 2026-08-13T09:25:37.405Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6376833816e848c3982fe815e96ac690 |
| 361 | 2026-08-13T09:25:37.610Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 362 | 2026-08-13T09:25:38.271Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6376833816e848c3982fe815e96ac690 |
| 363 | 2026-08-13T09:25:38.527Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 364 | 2026-08-13T09:25:48.369Z | proof_recorded |  |  | stage_id=check:d6e40bd565b02ef0; status=passed; cache_hit=False; input_fingerprint=677657ee769ee81ecedb8afbb3632b617fe7530198729cad3c4948d6e4160adf |
| 365 | 2026-08-13T09:25:49.052Z | proof_recorded |  |  | stage_id=check:d337118d6101b569; status=passed; cache_hit=False; input_fingerprint=90677950fda6f9c0ccad0cc0ba2e474628d792fa1b14d9010c1ab3bc5025e85a |
| 366 | 2026-08-13T09:25:49.458Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 367 | 2026-08-13T09:27:04.971Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d6e40bd565b02ef0 | passed | 677657ee769ee81ecedb8afbb3632b617fe7530198729cad3c4948d6e4160adf | False | 9079 | 0 |
| check:d337118d6101b569 | passed | 90677950fda6f9c0ccad0cc0ba2e474628d792fa1b14d9010c1ab3bc5025e85a | False | 236 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 2765d0fa0914416e8adf679762804f5b | accepted | a051897449827e4753b16def1b693d867fad76e9 | fbfa67aa81021d9494e2119e8a730c65aff83fb93798c7054fa9206f663a6ea3 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `8409c3c94e8c6aadb416c269c9f59c5abaa79f273d58743c12b6358dbcdff508`
