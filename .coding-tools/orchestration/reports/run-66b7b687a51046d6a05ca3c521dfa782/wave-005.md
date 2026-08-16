# Orchestration Wave 5

- Run: `66b7b687a51046d6a05ca3c521dfa782`
- Wave: `464c49c6d5844d7fa6ca6dfa968a3fbf`
- Objective: Replan Phase 3B after 37/38 focused tests passed but the standalone Recovery MCP test parsed an unexpected HTML response on the dynamically allocated port. Strengthen only the process oracle first: capture the spawned Recovery MCP stderr, require the child PID to still be alive after TCP readiness, GET /healthz from the same port and assert service='recovery-mcp' and pid==child.pid before making authenticated MCP requests. Make the generic HTTP helper preserve raw non-JSON bodies in assertion errors instead of throwing JSON.parse. Do not weaken Recovery MCP production behavior or auth assertions. Rerun py_compile and focused recovery-plane test.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `bc72311b66c8f7b3d77e3b8d0ecccdf84870bacc1d121a139166afbbe0f7cfaf`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6637 | 2026-08-16T09:01:26.854Z | wave_replanned |  | PREFLIGHT | reason=Final acceptance was rejected solely because canonical modified_files/receipt scope omitted core Phase 3B files first changed in a separate failed run. Preserve the proven design but make small meaningful observability/boundary annotations across every missing runtime source so the same run's final acceptance can hash all final Phase 3B bytes and the V2 auto-activation gate can authorize them. |
| 6638 | 2026-08-16T09:01:27.678Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6639 | 2026-08-16T09:01:28.418Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6640 | 2026-08-16T09:01:29.266Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6641 | 2026-08-16T09:01:29.919Z | state_transition | READY | ROUTED | reason=route_selected |
| 6642 | 2026-08-16T09:01:32.613Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9dde7ebe5f5c43579d922cf284161687 |
| 6643 | 2026-08-16T09:01:33.328Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6644 | 2026-08-16T09:01:33.777Z | managed_process_admitted |  |  | owner=default |
| 6645 | 2026-08-16T09:01:35.577Z | managed_process_started |  |  | owner=default |
| 6646 | 2026-08-16T09:01:36.826Z | managed_process_terminal |  |  | owner=default |
| 6647 | 2026-08-16T09:01:37.947Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9dde7ebe5f5c43579d922cf284161687 |
| 6648 | 2026-08-16T09:01:39.252Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6649 | 2026-08-16T09:01:41.475Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:25606f562d597b39; input_fingerprint=95b365b6c3153a221aa5a67300251826826bf2532ccafe0fcbaf0bfd15a83aea |
| 6650 | 2026-08-16T09:01:44.859Z | managed_process_admitted |  |  | owner=default |
| 6651 | 2026-08-16T09:01:46.243Z | managed_process_started |  |  | owner=default |
| 6652 | 2026-08-16T09:01:48.448Z | managed_process_terminal |  |  | owner=default |
| 6653 | 2026-08-16T09:01:50.184Z | proof_recorded |  |  | stage_id=check:25606f562d597b39; status=passed; cache_hit=False; input_fingerprint=95b365b6c3153a221aa5a67300251826826bf2532ccafe0fcbaf0bfd15a83aea |
| 6654 | 2026-08-16T09:01:51.540Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:45c86d0688b3516a; input_fingerprint=b0078845469a7403e43e8267ee0088ded3198cffde0216131dc22fb8f0aeac16 |
| 6655 | 2026-08-16T09:01:54.209Z | managed_process_admitted |  |  | owner=default |
| 6656 | 2026-08-16T09:01:55.616Z | managed_process_admitted |  |  | owner=default |
| 6657 | 2026-08-16T09:01:55.856Z | managed_process_started |  |  | owner=default |
| 6658 | 2026-08-16T09:01:57.640Z | managed_process_started |  |  | owner=default |
| 6659 | 2026-08-16T09:01:58.046Z | managed_process_terminal |  |  | owner=default |
| 6660 | 2026-08-16T09:01:59.736Z | managed_process_terminal |  |  | owner=default |
| 6661 | 2026-08-16T09:01:59.997Z | proof_recorded |  |  | stage_id=check:45c86d0688b3516a; status=passed; cache_hit=False; input_fingerprint=b0078845469a7403e43e8267ee0088ded3198cffde0216131dc22fb8f0aeac16 |
| 6662 | 2026-08-16T09:02:01.914Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:328e123c63857fd8; input_fingerprint=61e518eae1b2f46e3daeea299af3a6546f63e5716c49fe09556ca75fa1a69ffa |
| 6663 | 2026-08-16T09:02:04.909Z | managed_process_admitted |  |  | owner=default |
| 6664 | 2026-08-16T09:02:07.299Z | managed_process_started |  |  | owner=default |
| 6665 | 2026-08-16T09:02:17.783Z | managed_process_admitted |  |  | owner=default |
| 6666 | 2026-08-16T09:02:18.496Z | managed_process_terminal |  |  | owner=default |
| 6667 | 2026-08-16T09:02:18.965Z | managed_process_started |  |  | owner=default |
| 6668 | 2026-08-16T09:02:20.649Z | proof_recorded |  |  | stage_id=check:328e123c63857fd8; status=passed; cache_hit=False; input_fingerprint=61e518eae1b2f46e3daeea299af3a6546f63e5716c49fe09556ca75fa1a69ffa |
| 6669 | 2026-08-16T09:02:21.322Z | managed_process_terminal |  |  | owner=default |
| 6670 | 2026-08-16T09:02:22.878Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a09a76f914a04488; input_fingerprint=cde8b37281cbea8ad2032183c3c49420abfd430e292439c0aa09536a9156c00a |
| 6671 | 2026-08-16T09:02:26.348Z | managed_process_admitted |  |  | owner=default |
| 6672 | 2026-08-16T09:02:28.639Z | managed_process_started |  |  | owner=default |
| 6673 | 2026-08-16T09:02:31.009Z | managed_process_terminal |  |  | owner=default |
| 6674 | 2026-08-16T09:02:32.857Z | proof_recorded |  |  | stage_id=check:a09a76f914a04488; status=passed; cache_hit=False; input_fingerprint=cde8b37281cbea8ad2032183c3c49420abfd430e292439c0aa09536a9156c00a |
| 6675 | 2026-08-16T09:02:34.414Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=70d9082fb3f67f87fbae099b3cb987fd447a1858303471f4a2f97e38eadf6b3f |
| 6676 | 2026-08-16T09:02:37.435Z | managed_process_admitted |  |  | owner=default |
| 6677 | 2026-08-16T09:02:39.164Z | managed_process_started |  |  | owner=default |
| 6678 | 2026-08-16T09:02:50.808Z | managed_process_terminal |  |  | owner=default |
| 6679 | 2026-08-16T09:02:52.528Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=70d9082fb3f67f87fbae099b3cb987fd447a1858303471f4a2f97e38eadf6b3f |
| 6680 | 2026-08-16T09:02:53.998Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6681 | 2026-08-16T09:04:42.394Z | failure_observed | ACCEPTING | ACCEPTING | reason=Do not activate yet. Final provenance now covers 8 Phase 3B files but still omits resources/recovery-mcp/recovery_mcp.py, so its final accepted SHA receipt would be missing. Also, review found a fail-closed lifecycle edge: if a previously running Recovery Tunnel becomes not_configured, shares the primary tunnel ID, or loses its Runtime API key, ensureTunnel currently reports blocked/not_configured but can leave the old service-owned Recovery Tunnel PID alive. Replan to include Recovery MCP Python in final receipt scope and explicitly stop/null a stale owned Recovery Tunnel on invalid configuration, then re-prove.; failure_class=SOL_REJECTED |
| 6682 | 2026-08-16T09:04:43.467Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 6683 | 2026-08-16T09:04:47.535Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:25606f562d597b39 | passed | 95b365b6c3153a221aa5a67300251826826bf2532ccafe0fcbaf0bfd15a83aea | False | 6980 | 0 |
| check:45c86d0688b3516a | passed | b0078845469a7403e43e8267ee0088ded3198cffde0216131dc22fb8f0aeac16 | False | 6937 | 0 |
| check:328e123c63857fd8 | passed | 61e518eae1b2f46e3daeea299af3a6546f63e5716c49fe09556ca75fa1a69ffa | False | 16726 | 0 |
| check:a09a76f914a04488 | passed | cde8b37281cbea8ad2032183c3c49420abfd430e292439c0aa09536a9156c00a | False | 7901 | 0 |
| verify:tests | passed | 70d9082fb3f67f87fbae099b3cb987fd447a1858303471f4a2f97e38eadf6b3f | False | 16828 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `271`
- Chain head: `6e3848c269d200d6fca4d0162b782332078ef865e4cd623aea8368f5fef0422d`
