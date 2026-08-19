# Orchestration Wave 1

- Run: `df236f0e17d64e128bc0afd43443e225`
- Wave: `e8011ea85b68444ab38e0d80c0c9b471`
- Objective: Repair the concurrent execution-context isolation regression oracle only. Restore the quoted CODING_TOOLS_MCP_TOOL_MODE=smart environment mapping in test_background_worker_keeps_chatweb_execution_context, then run only test_workspace_session_isolation.py. Do not modify production source, measurement-integrity work, renderer, docs, telemetry, or any unrelated files. Do not commit, push, restart or deploy.
- Mode: `mcp_only`
- Base HEAD: `7c1c93ea72fa3465d718f7826494629426c1a9e8`
- Worktree fingerprint: `3b39e913d995db50091505ff43113061314eb7961bcd46c6a55dfbff51e13de6`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20206 | 2026-08-19T05:33:12.565Z | run_started |  | PREFLIGHT |  |
| 20207 | 2026-08-19T05:33:12.990Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20208 | 2026-08-19T05:33:13.132Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20209 | 2026-08-19T05:33:13.249Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20210 | 2026-08-19T05:33:13.463Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 20211 | 2026-08-19T05:33:13.618Z | state_transition | READY | ROUTED | reason=route_selected |
| 20212 | 2026-08-19T05:33:14.123Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9fff6dde6e294f89927bef288bea9f91 |
| 20213 | 2026-08-19T05:33:14.269Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20214 | 2026-08-19T05:33:14.887Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9fff6dde6e294f89927bef288bea9f91 |
| 20215 | 2026-08-19T05:33:15.044Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20216 | 2026-08-19T05:33:15.447Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=4cb963de1d1c6cba602268b476ec0d890c89efe771cabc86e9a6a1e206d91177 |
| 20217 | 2026-08-19T05:33:15.838Z | managed_process_admitted |  |  | owner=default |
| 20218 | 2026-08-19T05:33:16.250Z | managed_process_started |  |  | owner=default |
| 20219 | 2026-08-19T05:33:18.203Z | managed_process_admitted |  |  | owner=chatweb-isolation-fix |
| 20220 | 2026-08-19T05:33:18.555Z | managed_process_started |  |  | owner=chatweb-isolation-fix |
| 20221 | 2026-08-19T05:33:18.558Z | state_transition | PROVING | ABORTED | reason=task_cleared |
| 20222 | 2026-08-19T05:33:19.307Z | managed_process_terminal |  |  | owner=default |
| 20223 | 2026-08-19T05:33:19.637Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=4cb963de1d1c6cba602268b476ec0d890c89efe771cabc86e9a6a1e206d91177 |
| 20224 | 2026-08-19T05:33:19.718Z | managed_process_terminal |  |  | owner=chatweb-isolation-fix |
| 20225 | 2026-08-19T05:33:20.037Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |
| 20226 | 2026-08-19T05:33:20.237Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 20227 | 2026-08-19T05:33:29.671Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 20228 | 2026-08-19T05:33:30.081Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 4cb963de1d1c6cba602268b476ec0d890c89efe771cabc86e9a6a1e206d91177 | False | 3688 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5358549e487a47a39b06c173b799388e | accepted | 7c1c93ea72fa3465d718f7826494629426c1a9e8 | a1d6b803447c4e5e331174479bf8b5127548b0733069c6dd1247289b4b354c06 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `6203515414aa8dd264fa182a9211e9a96be05ea5ca60b119a0029cab27490461`
