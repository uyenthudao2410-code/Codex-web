# Orchestration Wave 2

- Run: `49f9c5e8ace04ae3a5d6ac6c8efbca47`
- Wave: `568afc7888ab4e8eb8f16694591fdc92`
- Objective: Fix the proven structured-process safety defect in crates/webcodex-core/src/shell_protocol.rs only. process_uses_shell_command_mode must reject the explicit command-text modes cmd.exe /K and PowerShell/pwsh -EncodedCommand in addition to the modes it already rejects. Extend the existing validate_process_argv shell-command-mode regression with exact /K and -EncodedCommand cases. Do not add speculative abbreviations or reject unrelated options. Keep P5 closed.
- Mode: `mcp_only`
- Base HEAD: `b7af2598297870e816dd131b0f73e0f77d7608d5`
- Worktree fingerprint: `477312abe47e56ebab728d244c002cf7e754f5a721fb474b2464ef1d852c9a7a`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 18585 | 2026-08-18T23:47:55.943Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 applied the intended one-file safety patch but rustfmt --check failed on one formatting-only delta in the PowerShell match arm. No semantic defect was reported and later proofs did not run. Repair strategy: apply exactly the retained rustfmt formatting delta, then run rustfmt --check, focused process_argv tests, cargo check -p webcodex-core, and exact diff-check without changing semantics or scope. |
| 18586 | 2026-08-18T23:48:00.942Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 18587 | 2026-08-18T23:48:16.636Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 18588 | 2026-08-18T23:48:16.785Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 18589 | 2026-08-18T23:48:16.911Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 18590 | 2026-08-18T23:48:17.019Z | state_transition | READY | ROUTED | reason=route_selected |
| 18591 | 2026-08-18T23:48:17.412Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7e8cde3c87da406cbdda4fa8490f5e52 |
| 18592 | 2026-08-18T23:48:17.536Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 18593 | 2026-08-18T23:48:17.917Z | solution_shadow_patch_surface_observed |  |  |  |
| 18594 | 2026-08-18T23:48:18.121Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7e8cde3c87da406cbdda4fa8490f5e52 |
| 18595 | 2026-08-18T23:48:18.242Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 18596 | 2026-08-18T23:48:18.600Z | proof_cache_miss |  |  | reason=cold; stage_id=check:de564d136649765f; input_fingerprint=8ddb99024244650f7d1c060be50dbb78e6409b03ad212bf2db76327251e2cc4e |
| 18597 | 2026-08-18T23:48:18.852Z | managed_process_admitted |  |  | owner=default |
| 18598 | 2026-08-18T23:48:19.085Z | managed_process_started |  |  | owner=default |
| 18599 | 2026-08-18T23:48:19.469Z | managed_process_terminal |  |  | owner=default |
| 18600 | 2026-08-18T23:48:19.720Z | proof_recorded |  |  | stage_id=check:de564d136649765f; status=passed; cache_hit=False; input_fingerprint=8ddb99024244650f7d1c060be50dbb78e6409b03ad212bf2db76327251e2cc4e |
| 18601 | 2026-08-18T23:48:19.842Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d2f147b0389a5acd; input_fingerprint=4b17e126c9c4f325cff7b361bb2831f526ce71b218aa70aec9ff9532ddc5d419 |
| 18602 | 2026-08-18T23:48:20.202Z | managed_process_admitted |  |  | owner=default |
| 18603 | 2026-08-18T23:48:20.486Z | managed_process_started |  |  | owner=default |
| 18604 | 2026-08-18T23:48:26.969Z | managed_process_terminal |  |  | owner=default |
| 18605 | 2026-08-18T23:48:27.312Z | proof_recorded |  |  | stage_id=check:d2f147b0389a5acd; status=passed; cache_hit=False; input_fingerprint=4b17e126c9c4f325cff7b361bb2831f526ce71b218aa70aec9ff9532ddc5d419 |
| 18606 | 2026-08-18T23:48:27.464Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:c14be7b9ffb554d1; input_fingerprint=10a0e62891dad324e0e36f8da0f74bfdcbea8629cddbda61cb02a8111065e794 |
| 18607 | 2026-08-18T23:48:27.753Z | managed_process_admitted |  |  | owner=default |
| 18608 | 2026-08-18T23:48:27.986Z | managed_process_started |  |  | owner=default |
| 18609 | 2026-08-18T23:48:30.952Z | managed_process_terminal |  |  | owner=default |
| 18610 | 2026-08-18T23:48:31.302Z | proof_recorded |  |  | stage_id=check:c14be7b9ffb554d1; status=passed; cache_hit=False; input_fingerprint=10a0e62891dad324e0e36f8da0f74bfdcbea8629cddbda61cb02a8111065e794 |
| 18611 | 2026-08-18T23:48:31.411Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:44e5db39d92d0f59; input_fingerprint=5d6c03a3aa7be840370bb04caad82b87246943ba399d276a201c1c2b6c88e7ea |
| 18612 | 2026-08-18T23:48:31.658Z | managed_process_admitted |  |  | owner=default |
| 18613 | 2026-08-18T23:48:31.878Z | managed_process_started |  |  | owner=default |
| 18614 | 2026-08-18T23:48:32.242Z | managed_process_terminal |  |  | owner=default |
| 18615 | 2026-08-18T23:48:32.468Z | proof_recorded |  |  | stage_id=check:44e5db39d92d0f59; status=passed; cache_hit=False; input_fingerprint=5d6c03a3aa7be840370bb04caad82b87246943ba399d276a201c1c2b6c88e7ea |
| 18616 | 2026-08-18T23:48:33.002Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 18617 | 2026-08-18T23:48:49.869Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 18618 | 2026-08-18T23:48:50.171Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:de564d136649765f | passed | 8ddb99024244650f7d1c060be50dbb78e6409b03ad212bf2db76327251e2cc4e | False | 865 | 0 |
| check:d2f147b0389a5acd | passed | 4b17e126c9c4f325cff7b361bb2831f526ce71b218aa70aec9ff9532ddc5d419 | False | 7189 | 0 |
| check:c14be7b9ffb554d1 | passed | 10a0e62891dad324e0e36f8da0f74bfdcbea8629cddbda61cb02a8111065e794 | False | 3510 | 0 |
| check:44e5db39d92d0f59 | passed | 5d6c03a3aa7be840370bb04caad82b87246943ba399d276a201c1c2b6c88e7ea | False | 821 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e1e42f1f494e4c618e5569334c032ceb | accepted | b7af2598297870e816dd131b0f73e0f77d7608d5 | 74d0fb388e0441187804046fdaebe7bba046613d95abceeda190573146521e2d | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `2abdba7870ddf013092c5fb47b9b5de59d78f9b41f43fb9640b2a52a3a8e4448`
