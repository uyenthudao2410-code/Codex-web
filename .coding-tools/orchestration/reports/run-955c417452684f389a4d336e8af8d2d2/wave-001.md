# Orchestration Wave 1

- Run: `955c417452684f389a4d336e8af8d2d2`
- Wave: `4d4d2c22ac824bfeb9385bc4bdeb5329`
- Objective: Inspect the exact current package.json after the Phase 3 provenance run entered REPLAN because its first proof command used forbidden node -e. Determine whether recovery:supervisor:once was already applied. Do not mutate anything. Preserve all other dirty/untracked work.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `9978fa9917c640cbfa56dfcc260755156143bb844b4bcd73e88b077edea60df1`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6928 | 2026-08-16T09:58:42.278Z | run_started |  | PREFLIGHT |  |
| 6929 | 2026-08-16T09:58:44.604Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6930 | 2026-08-16T09:59:02.422Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6931 | 2026-08-16T09:59:02.561Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6932 | 2026-08-16T09:59:02.671Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6933 | 2026-08-16T09:59:02.805Z | state_transition | READY | ROUTED | reason=route_selected |
| 6934 | 2026-08-16T09:59:03.172Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c3a66a4278e745d38684a2479dfea7b9 |
| 6935 | 2026-08-16T09:59:03.278Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6936 | 2026-08-16T09:59:03.680Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c3a66a4278e745d38684a2479dfea7b9 |
| 6937 | 2026-08-16T09:59:03.780Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6938 | 2026-08-16T09:59:04.080Z | proof_cache_miss |  |  | reason=cold; stage_id=check:de487489d6655339; input_fingerprint=b40afc041ef3d0911edba39254de9b104b1fb5ac58194e4d7b922ac6b988567a |
| 6939 | 2026-08-16T09:59:04.343Z | managed_process_admitted |  |  | owner=default |
| 6940 | 2026-08-16T09:59:04.559Z | managed_process_started |  |  | owner=default |
| 6941 | 2026-08-16T09:59:06.155Z | managed_process_terminal |  |  | owner=default |
| 6942 | 2026-08-16T09:59:06.409Z | proof_recorded |  |  | stage_id=check:de487489d6655339; status=passed; cache_hit=False; input_fingerprint=b40afc041ef3d0911edba39254de9b104b1fb5ac58194e4d7b922ac6b988567a |
| 6943 | 2026-08-16T09:59:06.556Z | proof_cache_miss |  |  | reason=cold; stage_id=check:97e7f1cbe2123e86; input_fingerprint=dca98415b01fa1f2e3f918e20029ad75510a07c43b685b6ff71c9c0cd4fbe015 |
| 6944 | 2026-08-16T09:59:06.794Z | managed_process_admitted |  |  | owner=default |
| 6945 | 2026-08-16T09:59:07.009Z | managed_process_started |  |  | owner=default |
| 6946 | 2026-08-16T09:59:07.338Z | managed_process_terminal |  |  | owner=default |
| 6947 | 2026-08-16T09:59:07.513Z | proof_recorded |  |  | stage_id=check:97e7f1cbe2123e86; status=passed; cache_hit=False; input_fingerprint=dca98415b01fa1f2e3f918e20029ad75510a07c43b685b6ff71c9c0cd4fbe015 |
| 6948 | 2026-08-16T09:59:07.607Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=1ca0e27834efbf89d66c11239a699189409873ad0ffac1b10d6876b0101ea49b |
| 6949 | 2026-08-16T09:59:07.851Z | managed_process_admitted |  |  | owner=default |
| 6950 | 2026-08-16T09:59:08.067Z | managed_process_started |  |  | owner=default |
| 6951 | 2026-08-16T09:59:25.654Z | managed_process_terminal |  |  | owner=default |
| 6952 | 2026-08-16T09:59:25.905Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=1ca0e27834efbf89d66c11239a699189409873ad0ffac1b10d6876b0101ea49b |
| 6953 | 2026-08-16T09:59:26.431Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6954 | 2026-08-16T09:59:46.142Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 6955 | 2026-08-16T09:59:46.442Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:de487489d6655339 | passed | b40afc041ef3d0911edba39254de9b104b1fb5ac58194e4d7b922ac6b988567a | False | 2101 | 0 |
| check:97e7f1cbe2123e86 | passed | dca98415b01fa1f2e3f918e20029ad75510a07c43b685b6ff71c9c0cd4fbe015 | False | 740 | 0 |
| verify:tests | passed | 1ca0e27834efbf89d66c11239a699189409873ad0ffac1b10d6876b0101ea49b | False | 18046 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 58f20e9f25c74ded96cea076ed5ebfc4 | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 5c9b838ea2886925a691302c065b4c2001eb4f5357063c7fe70f3f394155fc29 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `9e7bfab6ed3be0a8ad1d3563635dcad63e1a9887e7761f653f90d4e55877fb69`
