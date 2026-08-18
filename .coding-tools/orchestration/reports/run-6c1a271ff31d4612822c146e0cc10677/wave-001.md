# Orchestration Wave 1

- Run: `6c1a271ff31d4612822c146e0cc10677`
- Wave: `a5f4dec412144436be738f5627d0241d`
- Objective: P3 compute-placement control Layer B on the current exact checkout after accepted protocol contract checkpoint. Add typed optional compute_placement_policy selector only to cargo_check/cargo_test; thread it from ToolCall through cargo_tools into cargo validation request; update input/output schemas; update all compile-impacted ShellJobValidationMetadata literals with compute_placement: None. This layer must compile while leaving actual placement-routing behavior unchanged until Layer C. Preserve absent-selector behavior. Do not touch analyzer/frozen manifest, do not restart runtime, do not enroll representative P3 data, preserve all .coding-tools telemetry.
- Mode: `mcp_only`
- Base HEAD: `bc17700e475ce74c96a9547117aade58823f0811`
- Worktree fingerprint: `e43c8624f8231404f2f50edc357a4311476a975302e2d77bd54590924a7f87d8`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16161 | 2026-08-18T00:10:41.244Z | run_started |  | PREFLIGHT |  |
| 16162 | 2026-08-18T00:10:46.529Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16163 | 2026-08-18T00:12:00.490Z | managed_process_admitted |  |  | owner=default |
| 16164 | 2026-08-18T00:12:00.704Z | managed_process_started |  |  | owner=default |
| 16165 | 2026-08-18T00:12:01.304Z | managed_process_terminal |  |  | owner=default |
| 16166 | 2026-08-18T00:12:08.631Z | managed_process_admitted |  |  | owner=default |
| 16167 | 2026-08-18T00:12:08.837Z | managed_process_started |  |  | owner=default |
| 16168 | 2026-08-18T00:12:09.204Z | managed_process_terminal |  |  | owner=default |
| 16169 | 2026-08-18T00:12:48.214Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16170 | 2026-08-18T00:12:48.331Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16171 | 2026-08-18T00:12:48.448Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 16172 | 2026-08-18T00:12:48.570Z | state_transition | READY | ROUTED | reason=route_selected |
| 16173 | 2026-08-18T00:12:48.976Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b49e6e204bdf4098bc0d6e7577ecd8dd |
| 16174 | 2026-08-18T00:12:49.096Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16175 | 2026-08-18T00:12:49.592Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b49e6e204bdf4098bc0d6e7577ecd8dd |
| 16176 | 2026-08-18T00:12:49.706Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16177 | 2026-08-18T00:12:50.056Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b2ba44351432c945; input_fingerprint=073d9373a6cffe82bc63eb3cfd7317ba71cd9ec234fa8e8ff50b22128a59b890 |
| 16178 | 2026-08-18T00:12:50.298Z | managed_process_admitted |  |  | owner=default |
| 16179 | 2026-08-18T00:12:50.489Z | managed_process_started |  |  | owner=default |
| 16180 | 2026-08-18T00:12:50.864Z | managed_process_terminal |  |  | owner=default |
| 16181 | 2026-08-18T00:12:51.132Z | proof_recorded |  |  | stage_id=check:b2ba44351432c945; status=passed; cache_hit=False; input_fingerprint=073d9373a6cffe82bc63eb3cfd7317ba71cd9ec234fa8e8ff50b22128a59b890 |
| 16182 | 2026-08-18T00:12:51.252Z | proof_cache_miss |  |  | reason=cold; stage_id=check:669b573a6b473f98; input_fingerprint=426c6aee6fd4b88760112ab9fddf83c6183d41b47cfd2e85fd564f7f4cfb3c03 |
| 16183 | 2026-08-18T00:12:51.490Z | managed_process_admitted |  |  | owner=default |
| 16184 | 2026-08-18T00:12:51.707Z | managed_process_started |  |  | owner=default |
| 16185 | 2026-08-18T00:12:52.056Z | managed_process_terminal |  |  | owner=default |
| 16186 | 2026-08-18T00:12:52.302Z | proof_recorded |  |  | stage_id=check:669b573a6b473f98; status=passed; cache_hit=False; input_fingerprint=426c6aee6fd4b88760112ab9fddf83c6183d41b47cfd2e85fd564f7f4cfb3c03 |
| 16187 | 2026-08-18T00:12:52.750Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 16188 | 2026-08-18T00:13:02.009Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 16189 | 2026-08-18T00:13:02.265Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b2ba44351432c945 | passed | 073d9373a6cffe82bc63eb3cfd7317ba71cd9ec234fa8e8ff50b22128a59b890 | False | 850 | 0 |
| check:669b573a6b473f98 | passed | 426c6aee6fd4b88760112ab9fddf83c6183d41b47cfd2e85fd564f7f4cfb3c03 | False | 825 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 20637cbbb2f448f9aaad4f5df36d0c42 | accepted | bc17700e475ce74c96a9547117aade58823f0811 | 3960e2f532d1be0ad8d7a01e935a8142421b0efa4bbc291b428a07e13b2fc2b1 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `b3c0d6e7ea08405b45d6d332bc91962f7252d5e4a51ae6f597b0b260f19703ab`
