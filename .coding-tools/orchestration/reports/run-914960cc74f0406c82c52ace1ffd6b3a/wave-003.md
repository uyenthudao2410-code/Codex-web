# Orchestration Wave 3

- Run: `914960cc74f0406c82c52ace1ffd6b3a`
- Wave: `b8f926f426914df98de269bb09010c41`
- Objective: Continue Layer C after accepted C1a on the current authoritative checkout. Wire explicit compute_placement_policy guards into run_readonly_validation and run_readonly_validation_agent; explicit selector only for long unsandboxed Agent-backed structured-job capable clean exact-source cargo_check/test. Implement local_only forcing source with no remote target selection and server_preferred using existing clean target selection/revalidation plus source fallback. Build ShellJobValidationComputePlacement from actual executor, persist it in ShellJobValidationMetadata and ValidationHandoff. Do not yet add tests in this wave beyond compile proof; selector absent must preserve current auto-offload behavior. Preserve all telemetry/concurrent commits. No analyzer/manifest/restart/P3 enrollment.
- Mode: `mcp_only`
- Base HEAD: `17e87d34b159cbc175a77bb041e670000c9f7f4b`
- Worktree fingerprint: `0fc7eed85e7a9ca38aa69bd0bf4e3f8d2c8ef766080d4e45b7a82833f26c50f2`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16379 | 2026-08-18T00:32:14.799Z | wave_replanned |  | PREFLIGHT | reason=C2a source mutation is real and git diff --check passed; the only failed check was rustfmt formatting. Continue from retained source by running rustfmt in the next mutation wave and completing runtime semantics before compiling/testing. |
| 16380 | 2026-08-18T00:32:20.164Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16381 | 2026-08-18T00:33:54.046Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16382 | 2026-08-18T00:33:54.187Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16383 | 2026-08-18T00:33:54.337Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 16384 | 2026-08-18T00:33:54.504Z | state_transition | READY | ROUTED | reason=route_selected |
| 16385 | 2026-08-18T00:33:55.032Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7610740116c44ec59c565d91811f1656 |
| 16386 | 2026-08-18T00:33:55.271Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16387 | 2026-08-18T00:33:56.007Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7610740116c44ec59c565d91811f1656 |
| 16388 | 2026-08-18T00:33:56.152Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16389 | 2026-08-18T00:33:56.603Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:718b79fbd1bef7b9; input_fingerprint=f545298e8bd0264c00e98a34a8e1b338eaac7530c0d35c1764a9c695a6e1367e |
| 16390 | 2026-08-18T00:33:56.916Z | managed_process_admitted |  |  | owner=default |
| 16391 | 2026-08-18T00:33:57.224Z | managed_process_started |  |  | owner=default |
| 16392 | 2026-08-18T00:34:03.008Z | managed_process_terminal |  |  | owner=default |
| 16393 | 2026-08-18T00:34:03.363Z | proof_recorded |  |  | stage_id=check:718b79fbd1bef7b9; status=passed; cache_hit=False; input_fingerprint=f545298e8bd0264c00e98a34a8e1b338eaac7530c0d35c1764a9c695a6e1367e |
| 16394 | 2026-08-18T00:34:03.556Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=00489ad7bd43955a02840b4b55d71dadd3d6470d843d554735aa9a5afa22db88 |
| 16395 | 2026-08-18T00:34:03.931Z | managed_process_admitted |  |  | owner=default |
| 16396 | 2026-08-18T00:34:04.240Z | managed_process_started |  |  | owner=default |
| 16397 | 2026-08-18T00:34:09.701Z | managed_process_terminal |  |  | owner=default |
| 16398 | 2026-08-18T00:34:09.946Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=00489ad7bd43955a02840b4b55d71dadd3d6470d843d554735aa9a5afa22db88 |
| 16399 | 2026-08-18T00:34:10.052Z | proof_cache_miss |  |  | reason=cold; stage_id=check:227bd0cf8a04855c; input_fingerprint=e23360869d0763126609c8477d56a8e8033caea3b239530a06412a7235dc8fe0 |
| 16400 | 2026-08-18T00:34:10.314Z | managed_process_admitted |  |  | owner=default |
| 16401 | 2026-08-18T00:34:10.546Z | managed_process_started |  |  | owner=default |
| 16402 | 2026-08-18T00:34:10.937Z | managed_process_terminal |  |  | owner=default |
| 16403 | 2026-08-18T00:34:11.163Z | proof_recorded |  |  | stage_id=check:227bd0cf8a04855c; status=passed; cache_hit=False; input_fingerprint=e23360869d0763126609c8477d56a8e8033caea3b239530a06412a7235dc8fe0 |
| 16404 | 2026-08-18T00:34:11.309Z | proof_cache_miss |  |  | reason=cold; stage_id=check:586ac65f8024ef3b; input_fingerprint=1abe4a2013f9451244c3144e2d23e9aa11cdcfee9060ea42051c9aebb4a545db |
| 16405 | 2026-08-18T00:34:11.582Z | managed_process_admitted |  |  | owner=default |
| 16406 | 2026-08-18T00:34:11.798Z | managed_process_started |  |  | owner=default |
| 16407 | 2026-08-18T00:34:58.090Z | managed_process_terminal |  |  | owner=default |
| 16408 | 2026-08-18T00:34:58.430Z | proof_recorded |  |  | stage_id=check:586ac65f8024ef3b; status=passed; cache_hit=False; input_fingerprint=1abe4a2013f9451244c3144e2d23e9aa11cdcfee9060ea42051c9aebb4a545db |
| 16409 | 2026-08-18T00:34:58.979Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 16410 | 2026-08-18T00:35:15.488Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 16411 | 2026-08-18T00:35:15.733Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:718b79fbd1bef7b9 | passed | f545298e8bd0264c00e98a34a8e1b338eaac7530c0d35c1764a9c695a6e1367e | False | 6410 | 0 |
| check:810e75f0d3dee10e | passed | 00489ad7bd43955a02840b4b55d71dadd3d6470d843d554735aa9a5afa22db88 | False | 6100 | 0 |
| check:227bd0cf8a04855c | passed | e23360869d0763126609c8477d56a8e8033caea3b239530a06412a7235dc8fe0 | False | 879 | 0 |
| check:586ac65f8024ef3b | passed | 1abe4a2013f9451244c3144e2d23e9aa11cdcfee9060ea42051c9aebb4a545db | False | 46816 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 13931e17e80e4911914475787df46083 | accepted | 17e87d34b159cbc175a77bb041e670000c9f7f4b | f3f98bfba35450a395e433dda0ded97edf8448e0f546e3588678f67b628616d4 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `105`
- Chain head: `35dc75a3c181ef05008301c28a66e545f0d1f1626e437e6c88d18e4d60fcfe12`
