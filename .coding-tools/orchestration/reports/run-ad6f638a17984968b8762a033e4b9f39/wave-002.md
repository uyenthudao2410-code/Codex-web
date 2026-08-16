# Orchestration Wave 2

- Run: `ad6f638a17984968b8762a033e4b9f39`
- Wave: `243281a552e14530bd0309e337a8d197`
- Objective: Verify the current smart-v3 public tool names directly from Python source. Read-only; return only relevant source evidence and do not mutate runtime state.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `d9db58a4756dff999f425083d39977d6083fb6b8c51c70d48ca8b3c340966487`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 7155 | 2026-08-16T10:43:09.472Z | wave_replanned |  | PREFLIGHT | reason=After the accepted 45s timing fix, live canary produced new material evidence: OpenAI control-plane polling is successful, but recovery-plane state points at transient duplicate PIDs while TCP 18083 is owned by a different valid recovery tunnel process. Log timestamps show duplicate bind attempts every supervision cycle. This is a distinct ownership/adoption race, so the strategy now adds listener-owner identity fencing rather than changing readiness timing again. |
| 7156 | 2026-08-16T10:43:12.013Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 7157 | 2026-08-16T10:44:30.286Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 7158 | 2026-08-16T10:44:30.410Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 7159 | 2026-08-16T10:44:30.523Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 7160 | 2026-08-16T10:44:30.624Z | state_transition | READY | ROUTED | reason=route_selected |
| 7161 | 2026-08-16T10:44:30.990Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6d05bc377996461e84b166cc3bbfa213 |
| 7162 | 2026-08-16T10:44:31.098Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 7163 | 2026-08-16T10:44:31.499Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6d05bc377996461e84b166cc3bbfa213 |
| 7164 | 2026-08-16T10:44:31.591Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 7165 | 2026-08-16T10:44:32.068Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8d444d33922441a9; input_fingerprint=686b394114a1c9a1e9c5fbcb50b40da90b2acfb12f8d2d89651e4f4a8f914182 |
| 7166 | 2026-08-16T10:44:32.279Z | managed_process_admitted |  |  | owner=default |
| 7167 | 2026-08-16T10:44:32.491Z | managed_process_started |  |  | owner=default |
| 7168 | 2026-08-16T10:44:33.942Z | managed_process_terminal |  |  | owner=default |
| 7169 | 2026-08-16T10:44:34.165Z | proof_recorded |  |  | stage_id=check:8d444d33922441a9; status=passed; cache_hit=False; input_fingerprint=686b394114a1c9a1e9c5fbcb50b40da90b2acfb12f8d2d89651e4f4a8f914182 |
| 7170 | 2026-08-16T10:44:34.269Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:4e484c871a44ba1c; input_fingerprint=131790d68fa258bebbc080d3c7b2f12c1c3669f0ac50a40ef6aed200d84325cd |
| 7171 | 2026-08-16T10:44:34.508Z | managed_process_admitted |  |  | owner=default |
| 7172 | 2026-08-16T10:44:34.739Z | managed_process_started |  |  | owner=default |
| 7173 | 2026-08-16T10:44:35.026Z | managed_process_terminal |  |  | owner=default |
| 7174 | 2026-08-16T10:44:35.166Z | proof_recorded |  |  | stage_id=check:4e484c871a44ba1c; status=passed; cache_hit=False; input_fingerprint=131790d68fa258bebbc080d3c7b2f12c1c3669f0ac50a40ef6aed200d84325cd |
| 7175 | 2026-08-16T10:44:35.267Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a4208cf8d14f4c2b8d823f555a61006d60efdfd47a59089a37264ca604a63799 |
| 7176 | 2026-08-16T10:44:35.549Z | managed_process_admitted |  |  | owner=default |
| 7177 | 2026-08-16T10:44:35.775Z | managed_process_started |  |  | owner=default |
| 7178 | 2026-08-16T10:44:55.232Z | managed_process_terminal |  |  | owner=default |
| 7179 | 2026-08-16T10:44:55.440Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=a4208cf8d14f4c2b8d823f555a61006d60efdfd47a59089a37264ca604a63799 |
| 7180 | 2026-08-16T10:44:55.913Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 7181 | 2026-08-16T10:45:07.693Z | managed_process_admitted |  |  | owner=default |
| 7182 | 2026-08-16T10:45:07.899Z | managed_process_started |  |  | owner=default |
| 7183 | 2026-08-16T10:45:10.524Z | managed_process_terminal |  |  | owner=default |
| 7184 | 2026-08-16T10:45:21.817Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 7185 | 2026-08-16T10:45:22.098Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8d444d33922441a9 | passed | 686b394114a1c9a1e9c5fbcb50b40da90b2acfb12f8d2d89651e4f4a8f914182 | False | 1885 | 0 |
| check:4e484c871a44ba1c | passed | 131790d68fa258bebbc080d3c7b2f12c1c3669f0ac50a40ef6aed200d84325cd | False | 645 | 0 |
| verify:tests | passed | a4208cf8d14f4c2b8d823f555a61006d60efdfd47a59089a37264ca604a63799 | False | 19952 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 53f3a83632b34ce1a001d8f652445fcd | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | c3a290e1bd14171d466913c64d7425ae000cef4d67ea0b22bbb526d278ac353c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `14f7e8085d31c2cd61ba30065da287423b87439d89bee54536ff1c29ad354482`
