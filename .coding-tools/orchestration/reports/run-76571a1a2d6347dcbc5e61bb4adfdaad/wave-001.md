# Orchestration Wave 1

- Run: `76571a1a2d6347dcbc5e61bb4adfdaad`
- Wave: `32affdcc59214aba9fb8979c305e9e20`
- Objective: Implement the smallest coherent fresh-machine activation/package-currentness and footprint fix on main@9e752e34 without changing workspace resolution or weakening activation gates. Preserve the existing authoritative 10-minute activation/bootstrap expiry and Recovery Host resume semantics; do not synthesize ready_commit_digest and do not make Python fail early merely because snapshot_busy=false. Add focused regression coverage proving an active admission-closed Recovery Host epoch with no ready commit is resumed/finalized when valid and terminalized with ACTIVATION_REQUEST_EXPIRED at its durable deadline instead of looping indefinitely. Strengthen Windows packaged smoke/verification so a package cannot be considered valid unless the packaged Coding MCP public contract is the exact smart-v3 8-tool contract and critical current schemas (including task_context_id on task_control/workspace_context/agent_workflow where source declares them) match the current packaged source; this must detect stale/mixed MCP resources before installation. Reduce installed footprint safely by configuring Electron languages to en-US and vi only and excluding runtime-unused resources/coding-tools-mcp tests, benchmarks, and scripts from extraResources while preserving coding_tools_mcp, python_vendor, pyproject/runtime metadata, Recovery Host, Recovery MCP, tunnel/native semantic tools, native Python, and offline startup. Update packaged resource parity exclusion logic and build-verification tests to match. Do not delete any source or .coding-tools evidence and do not commit/push/restart/deploy. Run focused Node tests for recovery-host/build verification and any smoke-unit tests that do not require a new package; run git diff --check and report exact changed paths.
- Objective revision: `1`
- Objective SHA-256: `69486375fe86312ffcfb2e4a8a3d7ad59d56823804d8c5fd5563b57ac482bcc4`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41707 | 2026-09-06T05:59:04.960Z | run_started |  | PREFLIGHT |  |
| 41708 | 2026-09-06T05:59:05.414Z | observation_span_recorded |  |  |  |
| 41709 | 2026-09-06T05:59:05.862Z | solution_shadow_recommended |  |  |  |
| 41710 | 2026-09-06T05:59:06.088Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41711 | 2026-09-06T05:59:06.289Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41712 | 2026-09-06T05:59:06.510Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41713 | 2026-09-06T05:59:06.740Z | state_transition | READY | ROUTED | reason=route_selected |
| 41714 | 2026-09-06T05:59:07.049Z | observation_span_recorded |  |  |  |
| 41715 | 2026-09-06T05:59:08.542Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7cf1a770303b456c8b30549f64384edc |
| 41716 | 2026-09-06T05:59:08.844Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41717 | 2026-09-06T05:59:09.710Z | observation_span_recorded |  |  |  |
| 41718 | 2026-09-06T05:59:10.897Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7cf1a770303b456c8b30549f64384edc |
| 41719 | 2026-09-06T05:59:11.344Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41720 | 2026-09-06T05:59:12.487Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1f8b72d1dc36037e; input_fingerprint=f6f7ef84f6abf5b6bc329268d40833e099f8484e8e8f7e13877c18739f7a432e |
| 41721 | 2026-09-06T05:59:13.225Z | managed_process_admitted |  |  | owner=default |
| 41722 | 2026-09-06T05:59:13.708Z | managed_process_started |  |  | owner=default |
| 41727 | 2026-09-06T05:59:19.626Z | managed_process_terminal |  |  | owner=default |
| 41728 | 2026-09-06T05:59:20.034Z | proof_recorded |  |  | stage_id=check:1f8b72d1dc36037e; status=passed; cache_hit=False; input_fingerprint=f6f7ef84f6abf5b6bc329268d40833e099f8484e8e8f7e13877c18739f7a432e |
| 41729 | 2026-09-06T05:59:20.330Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=e533a5a2334058611249c136600fdaceba6370439a808dafaa6175d822a1f808 |
| 41730 | 2026-09-06T05:59:21.108Z | managed_process_admitted |  |  | owner=default |
| 41731 | 2026-09-06T05:59:21.702Z | managed_process_started |  |  | owner=default |
| 41732 | 2026-09-06T05:59:22.868Z | managed_process_terminal |  |  | owner=default |
| 41733 | 2026-09-06T05:59:23.252Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=e533a5a2334058611249c136600fdaceba6370439a808dafaa6175d822a1f808 |
| 41734 | 2026-09-06T05:59:23.448Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b94e8a768324dd058d0283e10f7647635c8bf06e02b0c40e33e2dc758ae2d4c5 |
| 41735 | 2026-09-06T05:59:23.935Z | managed_process_admitted |  |  | owner=default |
| 41736 | 2026-09-06T05:59:24.360Z | managed_process_started |  |  | owner=default |
| 41737 | 2026-09-06T06:00:52.666Z | managed_process_terminal |  |  | owner=default |
| 41738 | 2026-09-06T06:00:54.802Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b94e8a768324dd058d0283e10f7647635c8bf06e02b0c40e33e2dc758ae2d4c5 |
| 41739 | 2026-09-06T06:00:55.172Z | observation_span_recorded |  |  |  |
| 41740 | 2026-09-06T06:00:55.391Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1f8b72d1dc36037e | passed | f6f7ef84f6abf5b6bc329268d40833e099f8484e8e8f7e13877c18739f7a432e | False | 7043 | 0 |
| check:466c2f308b48c766 | passed | e533a5a2334058611249c136600fdaceba6370439a808dafaa6175d822a1f808 | False | 2302 | 0 |
| verify:tests | passed | b94e8a768324dd058d0283e10f7647635c8bf06e02b0c40e33e2dc758ae2d4c5 | False | 90812 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `a1c8f9cc8ece4374fb2c910530c898f41ec7cb7d15e5ed13fdfa0d2c8006828d`
