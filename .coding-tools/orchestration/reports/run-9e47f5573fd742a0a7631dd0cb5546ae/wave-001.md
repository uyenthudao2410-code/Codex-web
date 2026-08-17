# Orchestration Wave 1

- Run: `9e47f5573fd742a0a7631dd0cb5546ae`
- Wave: `41d4725a6bd54f15aeb917a4af49b26e`
- Objective: Final release-candidate code/test gate on the current accepted worktree. This is proof-only: do not modify source, docs, package metadata, runtime state, or generated product configuration, and do not start/restart/kill Electron, Coding MCP, Recovery MCP, tunnels, or provider processes. Verify the exact current worktree with: git diff --check; the complete Python MCP test suite; the real Recovery process E2E suite; production dependency audit; and the complete root npm test suite including source-root cleanliness. Do not invoke any paid/provider model traffic or routing canary. Preserve the three intentional tracked deletions of confirmed shell artifacts. If any source/test file drifts during the gate, fail closed rather than accepting mixed-fingerprint evidence.
- Mode: `mcp_only`
- Base HEAD: `bae2a0b4de9ac342c0d5d533d59a38386e1dc9ca`
- Worktree fingerprint: `a5dece641bf00bf7aabe0a637cf7394b1ffaed07d726bfddc7f17fcf2615a6c7`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13985 | 2026-08-17T11:48:57.721Z | run_started |  | PREFLIGHT |  |
| 13986 | 2026-08-17T11:48:58.466Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13987 | 2026-08-17T11:48:58.925Z | managed_process_admitted |  |  | owner=default |
| 13988 | 2026-08-17T11:48:59.283Z | managed_process_started |  |  | owner=default |
| 13989 | 2026-08-17T11:49:25.459Z | managed_process_terminal |  |  | owner=default |
| 13990 | 2026-08-17T11:49:25.668Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13991 | 2026-08-17T11:49:25.881Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13992 | 2026-08-17T11:49:26.141Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13993 | 2026-08-17T11:49:26.367Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 13994 | 2026-08-17T11:49:26.564Z | state_transition | READY | ROUTED | reason=route_selected |
| 13995 | 2026-08-17T11:49:27.249Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a29b7a6a2d2d44eba81ce044f0cbc5bb |
| 13996 | 2026-08-17T11:49:27.516Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13997 | 2026-08-17T11:49:28.265Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a29b7a6a2d2d44eba81ce044f0cbc5bb |
| 13998 | 2026-08-17T11:49:28.491Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13999 | 2026-08-17T11:49:28.981Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=4f34d107be6a6149dd79ae7c57ddbe218016048ab5d19d3d34537229939f9d8f |
| 14000 | 2026-08-17T11:49:29.409Z | managed_process_admitted |  |  | owner=default |
| 14001 | 2026-08-17T11:49:29.734Z | managed_process_started |  |  | owner=default |
| 14002 | 2026-08-17T11:49:30.708Z | managed_process_terminal |  |  | owner=default |
| 14003 | 2026-08-17T11:49:31.122Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=4f34d107be6a6149dd79ae7c57ddbe218016048ab5d19d3d34537229939f9d8f |
| 14004 | 2026-08-17T11:49:31.287Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0f15be06557006f6; input_fingerprint=24629c2e67a0d5db4e40d9602a24d8682c00eecf1fa827469982fe2d07b02de4 |
| 14005 | 2026-08-17T11:49:31.789Z | managed_process_admitted |  |  | owner=default |
| 14006 | 2026-08-17T11:49:32.166Z | managed_process_started |  |  | owner=default |
| 14007 | 2026-08-17T11:53:35.332Z | managed_process_terminal |  |  | owner=default |
| 14008 | 2026-08-17T11:53:35.865Z | proof_recorded |  |  | stage_id=check:0f15be06557006f6; status=passed; cache_hit=False; input_fingerprint=24629c2e67a0d5db4e40d9602a24d8682c00eecf1fa827469982fe2d07b02de4 |
| 14009 | 2026-08-17T11:53:36.033Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:ea9535a6d4fc623b; input_fingerprint=691bfea13093b122ae9257192276f8b42ece87c8bbee7c5c658a5c421d42f498 |
| 14010 | 2026-08-17T11:53:36.399Z | managed_process_admitted |  |  | owner=default |
| 14011 | 2026-08-17T11:53:36.699Z | managed_process_started |  |  | owner=default |
| 14012 | 2026-08-17T11:53:44.104Z | managed_process_terminal |  |  | owner=default |
| 14013 | 2026-08-17T11:53:44.496Z | proof_recorded |  |  | stage_id=check:ea9535a6d4fc623b; status=passed; cache_hit=False; input_fingerprint=691bfea13093b122ae9257192276f8b42ece87c8bbee7c5c658a5c421d42f498 |
| 14014 | 2026-08-17T11:53:44.703Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b5a7d0c1f9de6cbd; input_fingerprint=7621179db17c2097b9c14c1b1600a5e8aabe26b5cd6db4c27903c2e7d1b727f2 |
| 14015 | 2026-08-17T11:53:45.112Z | managed_process_admitted |  |  | owner=default |
| 14016 | 2026-08-17T11:53:45.448Z | managed_process_started |  |  | owner=default |
| 14017 | 2026-08-17T11:53:47.261Z | managed_process_terminal |  |  | owner=default |
| 14018 | 2026-08-17T11:53:47.617Z | proof_recorded |  |  | stage_id=check:b5a7d0c1f9de6cbd; status=passed; cache_hit=False; input_fingerprint=7621179db17c2097b9c14c1b1600a5e8aabe26b5cd6db4c27903c2e7d1b727f2 |
| 14019 | 2026-08-17T11:53:47.817Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=cfa892f6e0c1997b8eaac72729b3cad63a033c2d268637cc52a8177eda79accf |
| 14020 | 2026-08-17T11:53:48.198Z | managed_process_admitted |  |  | owner=default |
| 14021 | 2026-08-17T11:53:48.565Z | managed_process_started |  |  | owner=default |
| 14022 | 2026-08-17T11:54:12.750Z | managed_process_terminal |  |  | owner=default |
| 14023 | 2026-08-17T11:54:14.389Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=cfa892f6e0c1997b8eaac72729b3cad63a033c2d268637cc52a8177eda79accf |
| 14024 | 2026-08-17T11:54:14.583Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 14025 | 2026-08-17T11:56:31.512Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 14026 | 2026-08-17T11:56:31.905Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | 4f34d107be6a6149dd79ae7c57ddbe218016048ab5d19d3d34537229939f9d8f | False | 1742 | 0 |
| check:0f15be06557006f6 | passed | 24629c2e67a0d5db4e40d9602a24d8682c00eecf1fa827469982fe2d07b02de4 | False | 244170 | 0 |
| check:ea9535a6d4fc623b | passed | 691bfea13093b122ae9257192276f8b42ece87c8bbee7c5c658a5c421d42f498 | False | 8117 | 0 |
| check:b5a7d0c1f9de6cbd | passed | 7621179db17c2097b9c14c1b1600a5e8aabe26b5cd6db4c27903c2e7d1b727f2 | False | 2539 | 0 |
| verify:tests | passed | cfa892f6e0c1997b8eaac72729b3cad63a033c2d268637cc52a8177eda79accf | False | 26093 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e1cd00f307de4f4e95dff14417c82ff7 | accepted | 1516f0e5ebcf4086376bb5d144c5e70bbfcf383b | c2ea85467b61b0fd9e58c41b94ec64d6a88bec45c82c13fed7988e2a8f2f6a6d | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `2b38da894dbcc2d99d17dbd526050e4f618851b23c7cf767e9cf5970c4b1292f`
