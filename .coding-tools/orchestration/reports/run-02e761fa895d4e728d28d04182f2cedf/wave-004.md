# Orchestration Wave 4

- Run: `02e761fa895d4e728d28d04182f2cedf`
- Wave: `24f0289cac394f16956fc46a50b6e6e8`
- Objective: Apply TG1-TG12 Stage B V4 exact-write packet to the authoritative dirty workspace and prove changed behavior
- Objective revision: `1`
- Objective SHA-256: `c6c27efeac75b597e1360bddfedc0c9534eefcbb1fff629d86a30574faf3fa64`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `67e483cebe04c03788e5376d5c309751029a51ed47a15a9a74cc2a2a16fa2ee1`
- Contract fingerprint: `6bc9eaf623ada4b15c77f2926eb17a49dbcdb1606c407afddc97b9115ba397c1`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36121 | 2026-09-03T04:47:03.601Z | wave_replanned |  | PREFLIGHT | reason=The focused pytest proof already passed on the exact current source fingerprint. The next command was blocked before execution solely because ../../ was treated as a workspace escape. Preserve that valid proof and run only the three missing gates from repository root using contained paths. |
| 36122 | 2026-09-03T04:47:03.820Z | observation_span_recorded |  |  |  |
| 36123 | 2026-09-03T04:47:04.935Z | observation_span_recorded |  |  |  |
| 36124 | 2026-09-03T04:47:05.110Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36125 | 2026-09-03T04:47:05.269Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 36126 | 2026-09-03T04:47:05.485Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36127 | 2026-09-03T04:47:05.672Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36128 | 2026-09-03T04:47:05.858Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 36129 | 2026-09-03T04:47:06.034Z | state_transition | READY | ROUTED | reason=route_selected |
| 36130 | 2026-09-03T04:47:06.278Z | observation_span_recorded |  |  |  |
| 36131 | 2026-09-03T04:47:07.588Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a51ad75e71ae40f7b8718042b59b1bfb |
| 36132 | 2026-09-03T04:47:07.802Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36133 | 2026-09-03T04:47:08.729Z | observation_span_recorded |  |  |  |
| 36134 | 2026-09-03T04:47:09.089Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a51ad75e71ae40f7b8718042b59b1bfb |
| 36135 | 2026-09-03T04:47:09.248Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36136 | 2026-09-03T04:47:10.277Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:99822a7899270cff; input_fingerprint=4d9cfd763dcb90bcdcf2b400c22da19cd9409944fe85e0309cbe826412e4d0f4 |
| 36137 | 2026-09-03T04:47:10.693Z | managed_process_admitted |  |  | owner=default |
| 36138 | 2026-09-03T04:47:11.036Z | managed_process_started |  |  | owner=default |
| 36139 | 2026-09-03T04:47:11.550Z | managed_process_terminal |  |  | owner=default |
| 36140 | 2026-09-03T04:47:11.897Z | proof_recorded |  |  | stage_id=check:99822a7899270cff; status=passed; cache_hit=False; input_fingerprint=4d9cfd763dcb90bcdcf2b400c22da19cd9409944fe85e0309cbe826412e4d0f4 |
| 36141 | 2026-09-03T04:47:12.108Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9840051871779d79; input_fingerprint=c51040171894af9f7ad505f6653b6a2e31a87a83e9f4dc6111968cb53fb01591 |
| 36142 | 2026-09-03T04:47:12.437Z | managed_process_admitted |  |  | owner=default |
| 36143 | 2026-09-03T04:47:12.742Z | managed_process_started |  |  | owner=default |
| 36144 | 2026-09-03T04:47:13.285Z | managed_process_terminal |  |  | owner=default |
| 36145 | 2026-09-03T04:47:13.619Z | proof_recorded |  |  | stage_id=check:9840051871779d79; status=passed; cache_hit=False; input_fingerprint=c51040171894af9f7ad505f6653b6a2e31a87a83e9f4dc6111968cb53fb01591 |
| 36146 | 2026-09-03T04:47:13.807Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8fb236d2fbd85973; input_fingerprint=7aee1d550101105804b42924cce8d0014189cb9cb5af4a71347ad8b7bf1e9f12 |
| 36147 | 2026-09-03T04:47:14.258Z | managed_process_admitted |  |  | owner=default |
| 36148 | 2026-09-03T04:47:14.591Z | managed_process_started |  |  | owner=default |
| 36149 | 2026-09-03T04:47:15.085Z | managed_process_terminal |  |  | owner=default |
| 36150 | 2026-09-03T04:47:15.533Z | proof_recorded |  |  | stage_id=check:8fb236d2fbd85973; status=failed; cache_hit=False; input_fingerprint=7aee1d550101105804b42924cce8d0014189cb9cb5af4a71347ad8b7bf1e9f12 |
| 36151 | 2026-09-03T04:47:16.042Z | observation_span_recorded |  |  |  |
| 36152 | 2026-09-03T04:47:16.216Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 36153 | 2026-09-03T04:47:16.390Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 36154 | 2026-09-03T04:47:16.562Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:99822a7899270cff | passed | 4d9cfd763dcb90bcdcf2b400c22da19cd9409944fe85e0309cbe826412e4d0f4 | False | 1257 | 0 |
| check:9840051871779d79 | passed | c51040171894af9f7ad505f6653b6a2e31a87a83e9f4dc6111968cb53fb01591 | False | 1183 | 0 |
| check:8fb236d2fbd85973 | failed | 7aee1d550101105804b42924cce8d0014189cb9cb5af4a71347ad8b7bf1e9f12 | False | 1325 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `222`
- Chain head: `acc5c5cbb29137c03d5a1a3cc7eb065d17c4bf71f5f9072787acf4f4896feb6c`
