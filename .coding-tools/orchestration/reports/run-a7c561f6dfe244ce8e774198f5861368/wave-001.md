# Orchestration Wave 1

- Run: `a7c561f6dfe244ce8e774198f5861368`
- Wave: `78884ba7595644a39ee840f3fa1ab2e1`
- Objective: Add an always-on project workflow rule that prevents silent or abrupt endings after tool-call sequences. Every material work wave or batch must produce an operator-visible status checkpoint when it completes, when a blocker causes BLOCKED/REPLAN/ABORTED, before pause or handoff, and before the task/session stops. Tool cards or raw tool output alone are never a status report. Each checkpoint must state: completed/changed work; current Git/run/external-system state and strongest proof; blocker/failure classification when relevant; remaining work; exact next action. Long sequences should report at meaningful wave boundaries, not after every tool call. If work can continue, explicitly say it continues. If it cannot, state the exact approval/evidence/action needed. Preserve unrelated UI changes and volatile runtime evidence. Prefer updating the root always-on AGENTS.md; update an existing maintained orchestration guide only if one already exists and directly governs this behavior.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `c12de095d1bd9c71ffb3f7f18f1f669c6b6e8c98631542b3890623679604e0eb`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13212 | 2026-08-17T09:32:35.984Z | run_started |  | PREFLIGHT |  |
| 13213 | 2026-08-17T09:32:36.859Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13214 | 2026-08-17T09:33:38.579Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13215 | 2026-08-17T09:33:38.788Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13216 | 2026-08-17T09:33:38.987Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13217 | 2026-08-17T09:33:39.196Z | state_transition | READY | ROUTED | reason=route_selected |
| 13218 | 2026-08-17T09:33:39.987Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4159247fb5a24b4fa41caae20a7f4d48 |
| 13219 | 2026-08-17T09:33:40.249Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13220 | 2026-08-17T09:33:40.931Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4159247fb5a24b4fa41caae20a7f4d48 |
| 13221 | 2026-08-17T09:33:41.120Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13222 | 2026-08-17T09:33:41.641Z | proof_cache_miss |  |  | reason=cold; stage_id=check:867ae05e0eb34204; input_fingerprint=4a49c78e4e9b9e3cc479ce68b39426c1d8bcdaa080cdd29d753b8660d9bc7cbd |
| 13223 | 2026-08-17T09:33:42.037Z | managed_process_admitted |  |  | owner=default |
| 13224 | 2026-08-17T09:33:42.338Z | managed_process_started |  |  | owner=default |
| 13225 | 2026-08-17T09:33:42.849Z | managed_process_terminal |  |  | owner=default |
| 13226 | 2026-08-17T09:33:43.172Z | proof_recorded |  |  | stage_id=check:867ae05e0eb34204; status=passed; cache_hit=False; input_fingerprint=4a49c78e4e9b9e3cc479ce68b39426c1d8bcdaa080cdd29d753b8660d9bc7cbd |
| 13227 | 2026-08-17T09:33:43.354Z | proof_cache_miss |  |  | reason=cold; stage_id=check:21ffc093d68e984b; input_fingerprint=a050f46d12ceede73714c4b2d7d1953eb6af3e1c9d63b81564094db87516121e |
| 13228 | 2026-08-17T09:33:43.723Z | managed_process_admitted |  |  | owner=default |
| 13229 | 2026-08-17T09:33:44.067Z | managed_process_started |  |  | owner=default |
| 13230 | 2026-08-17T09:33:44.567Z | managed_process_terminal |  |  | owner=default |
| 13231 | 2026-08-17T09:33:44.921Z | proof_recorded |  |  | stage_id=check:21ffc093d68e984b; status=passed; cache_hit=False; input_fingerprint=a050f46d12ceede73714c4b2d7d1953eb6af3e1c9d63b81564094db87516121e |
| 13232 | 2026-08-17T09:33:45.486Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13233 | 2026-08-17T09:34:06.876Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13234 | 2026-08-17T09:34:07.403Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:867ae05e0eb34204 | passed | 4a49c78e4e9b9e3cc479ce68b39426c1d8bcdaa080cdd29d753b8660d9bc7cbd | False | 1196 | 0 |
| check:21ffc093d68e984b | passed | a050f46d12ceede73714c4b2d7d1953eb6af3e1c9d63b81564094db87516121e | False | 1233 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e0d61c64efb440f69402afb217d81393 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 17c7f69f025f3ab81e354921eadcdbdb5f68e5146a8291ec7b63410350734f2b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `c2460ed773640a2eb01740fd3e8f4d3fa7b7ddf3a97f7dcc984434a7887ae8ee`
