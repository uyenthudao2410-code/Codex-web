# Orchestration Wave 1

- Run: `6247675bd8c84a4691cb102d49e44e59`
- Wave: `5459f364af92440b80ffda7f643ee211`
- Objective: Continue the active C01/M02 host-side packaged installation lineage for RUN c939fa550f344c94b4f30352fe2cefe4 after reconnect. Replace the failed oversized single-command harness with short bounded commands: (1) preflight exact installer hash and snapshot current Recovery Host PID/instance; (2) run the accepted NSIS installer from a real current-user Interactive/Limited Windows Scheduled Task into E:\WebMcpAcceptanceHost-1.0.0 and require LastTaskResult=0; (3) prove from another Scheduled Task that the host-installed root/exe/packaged supervisor are visible and supervisor SHA matches 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab; (4) install packaged Recovery Supervisor using the host-visible installed script/executable/app-root; (5) prove manifest mode=packaged, executable/app_root exact, executable hash matches manifest, supervisor status healthy with live PID, Recovery Host PID+instance unchanged, and canonical Recovery Supervisor task present. Fail closed before reboot on any mismatch. No source edit, reboot, commit, push, release, publish, or deploy in this wave.
- Objective revision: `1`
- Objective SHA-256: `db26d624fb0d4915ea882ad262436a44cd54f5a1083f70ef4ff1ddc40dae88d8`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `50993da4aaaf75219274db5f7d577b30281b165b`
- Worktree fingerprint: `e0b09c7fb983216e08afc2ab2a72011be4bf42711884a9ad1f178556ea50aae8`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 59586 | 2026-09-15T11:01:58.883Z | run_started |  | PREFLIGHT |  |
| 59587 | 2026-09-15T11:01:59.607Z | observation_span_recorded |  |  |  |
| 59588 | 2026-09-15T11:02:00.563Z | observation_span_recorded |  |  |  |
| 59589 | 2026-09-15T11:02:00.827Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 59590 | 2026-09-15T11:02:01.043Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 59591 | 2026-09-15T11:02:01.212Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 59592 | 2026-09-15T11:02:01.561Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 59593 | 2026-09-15T11:02:01.853Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 59594 | 2026-09-15T11:02:02.182Z | state_transition | READY | ROUTED | reason=route_selected |
| 59595 | 2026-09-15T11:02:02.428Z | observation_span_recorded |  |  |  |
| 59596 | 2026-09-15T11:02:03.410Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=365ae39620c646fcb67a5dee204724e4 |
| 59597 | 2026-09-15T11:02:03.594Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 59598 | 2026-09-15T11:02:04.467Z | observation_span_recorded |  |  |  |
| 59599 | 2026-09-15T11:02:04.758Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=365ae39620c646fcb67a5dee204724e4 |
| 59600 | 2026-09-15T11:02:04.945Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 59601 | 2026-09-15T11:02:05.820Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5891df84780ef01f; input_fingerprint=7e7976ac805a0a5f93b9d3b6191d653589cccebf53d3d1624fd0aca54e7e7d88 |
| 59602 | 2026-09-15T11:02:06.217Z | managed_process_admitted |  |  | owner=default |
| 59603 | 2026-09-15T11:02:06.531Z | managed_process_started |  |  | owner=default |
| 59604 | 2026-09-15T11:02:08.109Z | managed_process_terminal |  |  | owner=default |
| 59605 | 2026-09-15T11:02:08.577Z | proof_recorded |  |  | stage_id=check:5891df84780ef01f; status=passed; cache_hit=False; input_fingerprint=7e7976ac805a0a5f93b9d3b6191d653589cccebf53d3d1624fd0aca54e7e7d88 |
| 59606 | 2026-09-15T11:02:08.763Z | proof_cache_miss |  |  | reason=cold; stage_id=check:29aa3f664c8d46d1; input_fingerprint=57b56d32379f44e86775511ffb4ad1e6799c2c371b9938a1e652771ad7238a63 |
| 59607 | 2026-09-15T11:02:09.167Z | managed_process_admitted |  |  | owner=default |
| 59608 | 2026-09-15T11:02:09.454Z | managed_process_started |  |  | owner=default |
| 59612 | 2026-09-15T11:03:18.236Z | managed_process_terminal |  |  | owner=default |
| 59613 | 2026-09-15T11:03:19.087Z | proof_recorded |  |  | stage_id=check:29aa3f664c8d46d1; status=passed; cache_hit=False; input_fingerprint=57b56d32379f44e86775511ffb4ad1e6799c2c371b9938a1e652771ad7238a63 |
| 59614 | 2026-09-15T11:03:19.923Z | proof_cache_miss |  |  | reason=cold; stage_id=check:47d05020941dad7e; input_fingerprint=d3cbfddfa4b7f97e0fb9c13d533f72e3a519918ff4f44922e2a6beadf0ae1217 |
| 59615 | 2026-09-15T11:03:21.319Z | managed_process_admitted |  |  | owner=default |
| 59616 | 2026-09-15T11:03:23.266Z | managed_process_started |  |  | owner=default |
| 59617 | 2026-09-15T11:03:27.810Z | managed_process_terminal |  |  | owner=default |
| 59618 | 2026-09-15T11:03:28.582Z | proof_recorded |  |  | stage_id=check:47d05020941dad7e; status=passed; cache_hit=False; input_fingerprint=d3cbfddfa4b7f97e0fb9c13d533f72e3a519918ff4f44922e2a6beadf0ae1217 |
| 59619 | 2026-09-15T11:03:28.942Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6e3a92a33bfed32c; input_fingerprint=5fe1915126155ca9033e428ddea9571aa54179c05d591b5a7f54d995dd108fbf |
| 59620 | 2026-09-15T11:03:29.622Z | managed_process_admitted |  |  | owner=default |
| 59621 | 2026-09-15T11:03:30.109Z | managed_process_started |  |  | owner=default |
| 59623 | 2026-09-15T11:03:38.446Z | managed_process_terminal |  |  | owner=default |
| 59624 | 2026-09-15T11:03:39.085Z | proof_recorded |  |  | stage_id=check:6e3a92a33bfed32c; status=passed; cache_hit=False; input_fingerprint=5fe1915126155ca9033e428ddea9571aa54179c05d591b5a7f54d995dd108fbf |
| 59625 | 2026-09-15T11:03:39.408Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4557bf7890647fcd; input_fingerprint=dfa35090f46d3667495732ec9986798760105b460e5b1d8432071bc07fd8a259 |
| 59626 | 2026-09-15T11:03:39.943Z | managed_process_admitted |  |  | owner=default |
| 59627 | 2026-09-15T11:03:40.517Z | managed_process_started |  |  | owner=default |
| 59628 | 2026-09-15T11:03:42.488Z | managed_process_terminal |  |  | owner=default |
| 59629 | 2026-09-15T11:03:42.990Z | proof_recorded |  |  | stage_id=check:4557bf7890647fcd; status=failed; cache_hit=False; input_fingerprint=dfa35090f46d3667495732ec9986798760105b460e5b1d8432071bc07fd8a259 |
| 59630 | 2026-09-15T11:03:43.267Z | observation_span_recorded |  |  |  |
| 59631 | 2026-09-15T11:03:43.584Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 59632 | 2026-09-15T11:03:43.914Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 59633 | 2026-09-15T11:03:44.228Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 59636 | 2026-09-15T11:04:15.835Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:5891df84780ef01f | passed | 7e7976ac805a0a5f93b9d3b6191d653589cccebf53d3d1624fd0aca54e7e7d88 | False | 2372 | 0 |
| check:29aa3f664c8d46d1 | passed | 57b56d32379f44e86775511ffb4ad1e6799c2c371b9938a1e652771ad7238a63 | False | 69756 | 0 |
| check:47d05020941dad7e | passed | d3cbfddfa4b7f97e0fb9c13d533f72e3a519918ff4f44922e2a6beadf0ae1217 | False | 7799 | 0 |
| check:6e3a92a33bfed32c | passed | 5fe1915126155ca9033e428ddea9571aa54179c05d591b5a7f54d995dd108fbf | False | 9455 | 0 |
| check:4557bf7890647fcd | failed | dfa35090f46d3667495732ec9986798760105b460e5b1d8432071bc07fd8a259 | False | 3076 | 14 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `c38e61b8770d847f78fee27b590b03abae062083822e0334edac680170151c03`
