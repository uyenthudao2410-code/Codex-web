# Orchestration Wave 1

- Run: `1498abb95ea64e27aeb19565f29cf244`
- Wave: `9d0d6e1b83b541fa8f5c9b83e5b23355`
- Objective: Resolve the reproduced controller-lease lifecycle failure that blocks C01 packaging. Determine whether tests/test_execution_hub_faults.py has a stale assertion or acceptance/finalization code violates the canonical terminal-run lease contract. Treat the current lifecycle invariant as authoritative only after comparing implementation plus tests: terminal accepted/CHECKPOINTED runs must not retain a stale controller lease; if historical-run acceptance needs a temporary reclaim, it must be released/terminalized consistently after acceptance. Make the smallest causal correction. Required proof: reproduce the exact failing historical-run acceptance test, apply only the causal change, rerun that test, then run the directly affected controller lease/lifecycle tests including the terminal-run lease test. Do not touch packaging/install/reboot/runtime restart/commit/push/release/deploy in this RUN.
- Objective revision: `1`
- Objective SHA-256: `7adbb0ebbed778f806b99e8f018551df0a2bd33f950c05f045fa465605629b3d`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `ae04947d5969e9ee92bf1fe7532bf30e186f8280`
- Worktree fingerprint: `74987f7ab6fe7151abc3dec844762710aad996d1d047389a538b2c603087ff73`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 55172 | 2026-09-14T13:47:53.160Z | run_started |  | PREFLIGHT |  |
| 55173 | 2026-09-14T13:47:53.776Z | observation_span_recorded |  |  |  |
| 55174 | 2026-09-14T13:47:59.225Z | observation_span_recorded |  |  |  |
| 55175 | 2026-09-14T13:47:59.405Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 55179 | 2026-09-14T13:49:09.321Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 55180 | 2026-09-14T13:49:09.676Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 55181 | 2026-09-14T13:49:09.913Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 55182 | 2026-09-14T13:49:10.086Z | state_transition | READY | ROUTED | reason=route_selected |
| 55185 | 2026-09-14T13:49:10.902Z | observation_span_recorded |  |  |  |
| 55187 | 2026-09-14T13:49:11.752Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cca5b06c2d8d4d408be883db5aa05570 |
| 55189 | 2026-09-14T13:49:12.164Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 55190 | 2026-09-14T13:49:12.788Z | patch_surface_observed |  |  |  |
| 55191 | 2026-09-14T13:49:13.030Z | observation_span_recorded |  |  |  |
| 55192 | 2026-09-14T13:49:13.055Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cca5b06c2d8d4d408be883db5aa05570 |
| 55193 | 2026-09-14T13:49:13.059Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 55194 | 2026-09-14T13:49:13.868Z | proof_cache_miss |  |  | reason=cold; stage_id=check:80f30999f4cbae86; input_fingerprint=066887f59c808da33ee5ad61f0a01687ed207ab6d7464bc86ef1bb6cc91ce085 |
| 55195 | 2026-09-14T13:49:14.436Z | managed_process_admitted |  |  | owner=default |
| 55196 | 2026-09-14T13:49:14.921Z | managed_process_started |  |  | owner=default |
| 55197 | 2026-09-14T13:49:25.315Z | managed_process_terminal |  |  | owner=default |
| 55198 | 2026-09-14T13:49:25.869Z | proof_recorded |  |  | stage_id=check:80f30999f4cbae86; status=passed; cache_hit=False; input_fingerprint=066887f59c808da33ee5ad61f0a01687ed207ab6d7464bc86ef1bb6cc91ce085 |
| 55199 | 2026-09-14T13:49:26.090Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d7805364acf835ff; input_fingerprint=59cf5125246339523609731763ad1641c07a3f80567e36a157fc2f3417c1935a |
| 55200 | 2026-09-14T13:49:26.659Z | managed_process_admitted |  |  | owner=default |
| 55201 | 2026-09-14T13:49:27.419Z | managed_process_started |  |  | owner=default |
| 55202 | 2026-09-14T13:49:31.129Z | managed_process_terminal |  |  | owner=default |
| 55203 | 2026-09-14T13:49:31.610Z | proof_recorded |  |  | stage_id=check:d7805364acf835ff; status=passed; cache_hit=False; input_fingerprint=59cf5125246339523609731763ad1641c07a3f80567e36a157fc2f3417c1935a |
| 55204 | 2026-09-14T13:49:31.872Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3b7b497a606b4425; input_fingerprint=9167596659cb65475d4955b7c23143d55b35029e1d3399a9219ca109f0816576 |
| 55205 | 2026-09-14T13:49:32.577Z | managed_process_admitted |  |  | owner=default |
| 55206 | 2026-09-14T13:49:33.060Z | managed_process_started |  |  | owner=default |
| 55207 | 2026-09-14T13:50:00.644Z | managed_process_terminal |  |  | owner=default |
| 55208 | 2026-09-14T13:50:01.126Z | proof_recorded |  |  | stage_id=check:3b7b497a606b4425; status=passed; cache_hit=False; input_fingerprint=9167596659cb65475d4955b7c23143d55b35029e1d3399a9219ca109f0816576 |
| 55209 | 2026-09-14T13:50:01.665Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4048c46656f816e7; input_fingerprint=4c54cf44e5cbf518a9674bcb8dde5f0689cc7507f891c1f2fb0b06732f326e68 |
| 55210 | 2026-09-14T13:50:02.328Z | managed_process_admitted |  |  | owner=default |
| 55211 | 2026-09-14T13:50:02.878Z | managed_process_started |  |  | owner=default |
| 55212 | 2026-09-14T13:50:56.734Z | managed_process_terminal |  |  | owner=default |
| 55213 | 2026-09-14T13:50:57.336Z | proof_recorded |  |  | stage_id=check:4048c46656f816e7; status=passed; cache_hit=False; input_fingerprint=4c54cf44e5cbf518a9674bcb8dde5f0689cc7507f891c1f2fb0b06732f326e68 |
| 55214 | 2026-09-14T13:50:58.253Z | observation_span_recorded |  |  |  |
| 55215 | 2026-09-14T13:50:58.729Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 55216 | 2026-09-14T13:50:59.093Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 55226 | 2026-09-14T13:51:11.020Z | managed_process_admitted |  |  | owner=default |
| 55227 | 2026-09-14T13:51:11.453Z | managed_process_started |  |  | owner=default |
| 55228 | 2026-09-14T13:51:12.020Z | managed_process_terminal |  |  | owner=default |
| 55229 | 2026-09-14T13:51:23.537Z | continuity_telemetry_recorded |  |  |  |
| 55230 | 2026-09-14T13:51:32.916Z | quality_outcome_recorded |  |  |  |
| 55231 | 2026-09-14T13:51:33.112Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 55232 | 2026-09-14T13:51:33.438Z | observation_span_recorded |  |  |  |
| 55233 | 2026-09-14T13:51:33.673Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 55234 | 2026-09-14T13:51:33.954Z | observation_span_recorded |  |  |  |
| 55235 | 2026-09-14T13:51:34.622Z | observation_span_recorded |  |  |  |
| 55236 | 2026-09-14T13:51:34.823Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:80f30999f4cbae86 | passed | 066887f59c808da33ee5ad61f0a01687ed207ab6d7464bc86ef1bb6cc91ce085 | False | 11615 | 0 |
| check:d7805364acf835ff | passed | 59cf5125246339523609731763ad1641c07a3f80567e36a157fc2f3417c1935a | False | 5052 | 0 |
| check:3b7b497a606b4425 | passed | 9167596659cb65475d4955b7c23143d55b35029e1d3399a9219ca109f0816576 | False | 28651 | 0 |
| check:4048c46656f816e7 | passed | 4c54cf44e5cbf518a9674bcb8dde5f0689cc7507f891c1f2fb0b06732f326e68 | False | 55118 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 73497e0ebe3c43f8ae4dbc5245525a47 | accepted | ae04947d5969e9ee92bf1fe7532bf30e186f8280 | 6fe48ebc4a1da21b72e1ee4c7a7581abc9ea88417bc502392b7aeb47a498d1ec | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `49`
- Chain head: `27213c7e3fad25683c4f50dcc2c129ad9e368155cc3f6d490fa0d77f5d5653d3`
