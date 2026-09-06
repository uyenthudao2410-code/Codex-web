# Orchestration Wave 2

- Run: `d623321a8ad542fc9592040eaa0a1976`
- Wave: `7645d1e894444b8aaa7c499e393c770f`
- Objective: Implement the bounded Codex-web 1.0 finish-line optimization on current main f702c2a without changing the public 8-tool smart-v3 contract or weakening EOCL/activation safety. Make dev and packaged Electron UI materially lighter: in renderer/browser.js, renderer/control-center.js, renderer/panel.js and renderer/dashboard.js prevent overlapping async polls, back off noncritical polling when the document/window is hidden or unfocused, avoid redundant unchanged DOM/render work where the current structure permits, and keep active-task/health refresh responsive when visible. In electron/chatViewController.js consolidate/debounce repeated chat UI enhancement scheduling/MutationObserver-triggered work so hidden/unchanged pages do not repeatedly rescan/rewrite the DOM; do not alter chat semantics. Preserve correctness-critical lease/heartbeat/recovery timers. Reduce Windows package footprint using supported electron-builder configuration to ship only en-US and vi locales and exclude only runtime-unused resources/coding-tools-mcp/tests, benchmarks and scripts from extraResources; retain coding_tools_mcp, python_vendor, Python/runtime launchers, Recovery Host, tunnel and native semantic/offline behavior. Strengthen scripts/verify-packaged-resources.js and tests/build-verification.test.js (or the closest existing package oracle) so packaged output must contain the current runtime entrypoints/public smart-v3 contract and must not contain the excluded dev-only payload/locales. Do not fake READY commits or force activation gates open; activation behavior remains fail-closed. Preserve all .coding-tools runtime/evidence and unrelated files. Add/update focused regression tests for the changed UI scheduling/package behavior where practical. Finish the wave only if focused tests and git diff --check pass; otherwise return a typed replan with exact failures.
- Objective revision: `1`
- Objective SHA-256: `747e6576043375b241968a53a4d6b36f56ae3c5b7b748cf1940f7410e43a565b`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `f702c2a4036d1d185337c14fe1f5cd03e14e3409`
- Worktree fingerprint: `31640b20c26b036f4ffacee3c36f92a0058a54d3b621ee34a6cdffc9f3c30974`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41852 | 2026-09-06T06:20:42.680Z | wave_replanned |  | PREFLIGHT | reason=The prior wave failed before mutation because deterministic route was paired with deep_single_lane. The operator report was presented and acknowledged. Continue the same RUN with mcp_only; source, objective, scope, and focused baseline remain unchanged and clean. |
| 41853 | 2026-09-06T06:20:42.917Z | observation_span_recorded |  |  |  |
| 41854 | 2026-09-06T06:20:46.800Z | observation_span_recorded |  |  |  |
| 41855 | 2026-09-06T06:20:47.034Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41856 | 2026-09-06T06:20:47.484Z | managed_process_admitted |  |  | owner=default |
| 41857 | 2026-09-06T06:20:47.809Z | managed_process_started |  |  | owner=default |
| 41858 | 2026-09-06T06:20:53.592Z | managed_process_terminal |  |  | owner=default |
| 41859 | 2026-09-06T06:20:53.835Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41860 | 2026-09-06T06:20:54.107Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41861 | 2026-09-06T06:20:54.311Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41862 | 2026-09-06T06:20:54.483Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41863 | 2026-09-06T06:20:54.672Z | state_transition | READY | ROUTED | reason=route_selected |
| 41864 | 2026-09-06T06:20:54.902Z | observation_span_recorded |  |  |  |
| 41865 | 2026-09-06T06:20:55.824Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c04a68af769147e0a00bc9c2c25162c3 |
| 41866 | 2026-09-06T06:20:56.023Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41867 | 2026-09-06T06:20:56.932Z | observation_span_recorded |  |  |  |
| 41868 | 2026-09-06T06:20:57.224Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c04a68af769147e0a00bc9c2c25162c3 |
| 41869 | 2026-09-06T06:20:57.375Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41870 | 2026-09-06T06:20:58.289Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=bc67c544e8b6393673abe686c260f2dcbb3597d34847386d911f67e54d7aed5b |
| 41871 | 2026-09-06T06:20:58.666Z | managed_process_admitted |  |  | owner=default |
| 41872 | 2026-09-06T06:20:58.984Z | managed_process_started |  |  | owner=default |
| 41873 | 2026-09-06T06:21:04.593Z | managed_process_terminal |  |  | owner=default |
| 41874 | 2026-09-06T06:21:06.036Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=bc67c544e8b6393673abe686c260f2dcbb3597d34847386d911f67e54d7aed5b |
| 41875 | 2026-09-06T06:21:06.314Z | observation_span_recorded |  |  |  |
| 41876 | 2026-09-06T06:21:06.508Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41952 | 2026-09-06T08:02:13.546Z | quality_outcome_recorded |  |  |  |
| 41953 | 2026-09-06T08:02:13.762Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 41954 | 2026-09-06T08:02:14.045Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | bc67c544e8b6393673abe686c260f2dcbb3597d34847386d911f67e54d7aed5b | False | 7328 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 359b6c09493f498b8e06bc34194b0c5b | accepted | 58ee20d3a5b2607016b1880f4276437eb2dcf5df | c8163b341fa6094fe5b3af651c3e28ac5946aa01c6cbc8c32a33c043c56d7d72 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `41`
- Chain head: `a10a005af29c50c99e957d3a54bee960636d696b58620cd494a97ff0b7325f10`
