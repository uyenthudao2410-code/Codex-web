# Orchestration Wave 1

- Run: `52f38c82d9cb4ac4b8b1f581e2ea3698`
- Wave: `a58f63876a5648c29f14706b68192773`
- Objective: Run the final read-only decision-science reports on the current repaired worktree without mutating source or opening treatment. Produce accepted-result economics, P2 stratified rework diagnosis, organic rework baseline, P4 readiness/P5 gate, and P5 baseline. Treat readiness nonzero exit as a gate result, not permission to alter policy. Preserve treatment, automatic activation/promotion, auto routing, auto handoff, and global server-first as OFF.
- Objective revision: `1`
- Objective SHA-256: `dedfee59515d93ed0cadaf6f2261e7a19c933e936bcf03b0ecb5229309f7d422`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e150020a0c0829a988ffea527d5c8d82132ed65`
- Worktree fingerprint: `7b54aa5ab96a3b29ba50523d4283c0e0553d039c6634fd3c18da1cfeab1344ff`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28539 | 2026-08-23T04:47:51.114Z | run_started |  | PREFLIGHT |  |
| 28540 | 2026-08-23T04:47:52.154Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 28541 | 2026-08-23T04:47:52.314Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 28542 | 2026-08-23T04:47:52.485Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28543 | 2026-08-23T04:47:52.634Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28544 | 2026-08-23T04:47:52.832Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 28545 | 2026-08-23T04:47:52.999Z | state_transition | READY | ROUTED | reason=route_selected |
| 28546 | 2026-08-23T04:47:53.792Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2be0297a9fea471b8a93cff10333f81b |
| 28547 | 2026-08-23T04:47:53.934Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28548 | 2026-08-23T04:47:54.734Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2be0297a9fea471b8a93cff10333f81b |
| 28549 | 2026-08-23T04:47:54.894Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28550 | 2026-08-23T04:47:55.734Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6c8bc5c786a91187; input_fingerprint=834249d802fde08d756a46302fc80aefad2aebd13b3164d3489815031522c94b |
| 28551 | 2026-08-23T04:47:56.054Z | managed_process_admitted |  |  | owner=default |
| 28552 | 2026-08-23T04:47:56.390Z | managed_process_started |  |  | owner=default |
| 28553 | 2026-08-23T04:47:58.881Z | managed_process_terminal |  |  | owner=default |
| 28554 | 2026-08-23T04:47:59.204Z | proof_recorded |  |  | stage_id=check:6c8bc5c786a91187; status=passed; cache_hit=False; input_fingerprint=834249d802fde08d756a46302fc80aefad2aebd13b3164d3489815031522c94b |
| 28555 | 2026-08-23T04:47:59.389Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5595442dfe9ea607; input_fingerprint=6ab52ff5b53eeb4c481d1361d06d1b2e755292b094288511f1e2db6c91b7f4e1 |
| 28556 | 2026-08-23T04:47:59.801Z | managed_process_admitted |  |  | owner=default |
| 28557 | 2026-08-23T04:48:00.162Z | managed_process_started |  |  | owner=default |
| 28558 | 2026-08-23T04:48:25.139Z | managed_process_terminal |  |  | owner=default |
| 28559 | 2026-08-23T04:48:25.478Z | proof_recorded |  |  | stage_id=check:5595442dfe9ea607; status=passed; cache_hit=False; input_fingerprint=6ab52ff5b53eeb4c481d1361d06d1b2e755292b094288511f1e2db6c91b7f4e1 |
| 28560 | 2026-08-23T04:48:25.718Z | proof_cache_miss |  |  | reason=cold; stage_id=check:609a403eb19cc380; input_fingerprint=f6fb1e3c295b5ecf226012a68d9432a9c540dbec4a639e6379e57d888bcafd24 |
| 28561 | 2026-08-23T04:48:26.050Z | managed_process_admitted |  |  | owner=default |
| 28562 | 2026-08-23T04:48:26.374Z | managed_process_started |  |  | owner=default |
| 28563 | 2026-08-23T04:48:27.365Z | managed_process_terminal |  |  | owner=default |
| 28564 | 2026-08-23T04:48:27.749Z | proof_recorded |  |  | stage_id=check:609a403eb19cc380; status=passed; cache_hit=False; input_fingerprint=f6fb1e3c295b5ecf226012a68d9432a9c540dbec4a639e6379e57d888bcafd24 |
| 28565 | 2026-08-23T04:48:27.894Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3a2b742deea614f6; input_fingerprint=9f033a67362de257f139219d46a92734bf1c44e524314d319dbe3cd1b228782e |
| 28566 | 2026-08-23T04:48:28.239Z | managed_process_admitted |  |  | owner=default |
| 28567 | 2026-08-23T04:48:28.578Z | managed_process_started |  |  | owner=default |
| 28568 | 2026-08-23T04:48:30.835Z | managed_process_terminal |  |  | owner=default |
| 28569 | 2026-08-23T04:48:31.245Z | proof_recorded |  |  | stage_id=check:3a2b742deea614f6; status=failed; cache_hit=False; input_fingerprint=9f033a67362de257f139219d46a92734bf1c44e524314d319dbe3cd1b228782e |
| 28570 | 2026-08-23T04:48:31.429Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 28571 | 2026-08-23T04:48:31.614Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 28572 | 2026-08-23T04:48:31.810Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6c8bc5c786a91187 | passed | 834249d802fde08d756a46302fc80aefad2aebd13b3164d3489815031522c94b | False | 3142 | 0 |
| check:5595442dfe9ea607 | passed | 6ab52ff5b53eeb4c481d1361d06d1b2e755292b094288511f1e2db6c91b7f4e1 | False | 25728 | 0 |
| check:609a403eb19cc380 | passed | f6fb1e3c295b5ecf226012a68d9432a9c540dbec4a639e6379e57d888bcafd24 | False | 1672 | 0 |
| check:3a2b742deea614f6 | failed | 9f033a67362de257f139219d46a92734bf1c44e524314d319dbe3cd1b228782e | False | 2929 | 4 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `a98967b99898e0a9cf67cd8cd700eb32f179ae5b3b1b9d6ce43d448092c6eb48`
