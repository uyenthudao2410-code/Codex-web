# Orchestration Wave 1

- Run: `2dcd84d110234763a34ca0670b3157b3`
- Wave: `e436293315de4f4dbb459e9c311b9f0f`
- Objective: G2-P12 provenance closure ONLY for the exact current Codex provider token-usage receipt packet. Adopt without changing source bytes exactly resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py SHA-256 e5a914c4d26725d176d99d1c4603f4a946aed258f5a81d8aa5d48ceb77cf8e1b and resources/coding-tools-mcp/tests/test_codex_bridge.py SHA-256 b98c4b5566ad5c6feb58c4b576503f4886640891c8767dabe72ffed76ec2ed45. Causal objective: Codex provider receipt exposes exact token fields only when complete and internally valid; bool, negative, incomplete, or impossible cached/reasoning/token totals fail closed as missing/invalid rather than plausible zero; accepted exact usage provenance is provider_reported. Preserve dirty worktree and all .coding-tools evidence. No source outside these two paths; no direct SQLite; no stale-RUN reconciliation; no bulk adopt; no synthetic Problems/outcomes; no reset/restore/clean/rebase; no secret output; no commit/push/tag/release/publish/deploy.
- Objective revision: `1`
- Objective SHA-256: `34d7aeae3d8fb83c1a6c10c0b2f74d059933050e6f4ad5901173636589b96b61`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38436 | 2026-09-03T18:02:21.162Z | run_started |  | PREFLIGHT |  |
| 38437 | 2026-09-03T18:02:21.577Z | observation_span_recorded |  |  |  |
| 38438 | 2026-09-03T18:02:22.473Z | observation_span_recorded |  |  |  |
| 38439 | 2026-09-03T18:02:22.748Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38440 | 2026-09-03T18:02:22.970Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38441 | 2026-09-03T18:02:23.162Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38442 | 2026-09-03T18:02:23.380Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38443 | 2026-09-03T18:02:23.598Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38444 | 2026-09-03T18:02:23.812Z | state_transition | READY | ROUTED | reason=route_selected |
| 38445 | 2026-09-03T18:02:24.021Z | observation_span_recorded |  |  |  |
| 38446 | 2026-09-03T18:02:25.048Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8b42a27f323544b4b34ac474adf187d4 |
| 38447 | 2026-09-03T18:02:25.250Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38448 | 2026-09-03T18:02:26.148Z | existing_file_adoption_observed |  |  |  |
| 38449 | 2026-09-03T18:02:26.378Z | observation_span_recorded |  |  |  |
| 38450 | 2026-09-03T18:02:26.689Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8b42a27f323544b4b34ac474adf187d4 |
| 38451 | 2026-09-03T18:02:26.886Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38452 | 2026-09-03T18:02:27.836Z | proof_cache_miss |  |  | reason=cold; stage_id=check:06f85350432a40e2; input_fingerprint=30df4ecf1add5555e5576de484e6c5dc8e22df81d3d9985213309d18326fc490 |
| 38453 | 2026-09-03T18:02:28.262Z | managed_process_admitted |  |  | owner=default |
| 38454 | 2026-09-03T18:02:28.621Z | managed_process_started |  |  | owner=default |
| 38455 | 2026-09-03T18:02:29.073Z | managed_process_terminal |  |  | owner=default |
| 38456 | 2026-09-03T18:02:29.458Z | proof_recorded |  |  | stage_id=check:06f85350432a40e2; status=passed; cache_hit=False; input_fingerprint=30df4ecf1add5555e5576de484e6c5dc8e22df81d3d9985213309d18326fc490 |
| 38457 | 2026-09-03T18:02:29.701Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0f08897aef24439f; input_fingerprint=325161bcee68377411198c26881e4a3c6ea4c0ac66541199802b64ad1b75746f |
| 38458 | 2026-09-03T18:02:30.172Z | managed_process_admitted |  |  | owner=default |
| 38459 | 2026-09-03T18:02:30.548Z | managed_process_started |  |  | owner=default |
| 38460 | 2026-09-03T18:02:31.521Z | managed_process_terminal |  |  | owner=default |
| 38461 | 2026-09-03T18:02:31.900Z | proof_recorded |  |  | stage_id=check:0f08897aef24439f; status=passed; cache_hit=False; input_fingerprint=325161bcee68377411198c26881e4a3c6ea4c0ac66541199802b64ad1b75746f |
| 38462 | 2026-09-03T18:02:32.129Z | observation_span_recorded |  |  |  |
| 38463 | 2026-09-03T18:02:32.428Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38464 | 2026-09-03T18:02:49.950Z | quality_outcome_recorded |  |  |  |
| 38465 | 2026-09-03T18:02:50.166Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38466 | 2026-09-03T18:02:50.598Z | observation_span_recorded |  |  |  |
| 38467 | 2026-09-03T18:02:50.854Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:06f85350432a40e2 | passed | 30df4ecf1add5555e5576de484e6c5dc8e22df81d3d9985213309d18326fc490 | False | 1223 | 0 |
| check:0f08897aef24439f | passed | 325161bcee68377411198c26881e4a3c6ea4c0ac66541199802b64ad1b75746f | False | 1758 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f6cd4a3ae78b4676831700ad73df9f56 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 821a1bc6b881b908690f1633a7d7ced553c826b2c6417bc4243e40e36f7c8f7a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `b8b28396e329dce3b5d23a4d740a206933547edd01bd3eddd0c4f59dae7a50cb`
