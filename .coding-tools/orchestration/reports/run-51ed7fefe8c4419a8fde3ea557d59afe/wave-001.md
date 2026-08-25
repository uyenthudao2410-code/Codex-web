# Orchestration Wave 1

- Run: `51ed7fefe8c4419a8fde3ea557d59afe`
- Wave: `be3552d34c1640c38ea023662ee153f6`
- Objective: Diagnose why after the operator closes/stops the Electron development session launched by `npm start`, a project tray/background app still appears to run, and whether this can cause new source changes to appear not updated. Determine the exact ownership/lifecycle relationship among npm/electron UI, Recovery Host, Coding MCP, tunnel, detached child processes, Electron UI auto-recovery, revision capture/activation, and dev-mode relaunch. Inspect current live status only through read-only supported commands. Identify whether an old Electron/Recovery Host instance can keep serving stale JS/renderer source after `npm start` exits, what components reload automatically vs require controlled activation, and the safest durable fix that preserves recovery reliability while giving development mode deterministic stop/reload semantics. Do not modify files, kill processes, restart services, acknowledge connector discovery, commit, or push.
- Objective revision: `1`
- Objective SHA-256: `988e1fc30103ff896f8b238a2c364d2a8db693181f098258f33ef2cfad974d9a`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `026f79b3ab5997cb15f38a3b41769da6a79d790b`
- Worktree fingerprint: `c4d9c59e1c80da2f34c680461b6dfe3855bc7820f396690ae0242a8871b95a69`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 29290 | 2026-08-25T07:31:40.629Z | run_started |  | PREFLIGHT |  |
| 29291 | 2026-08-25T07:31:40.846Z | observation_span_recorded |  |  |  |
| 29292 | 2026-08-25T07:31:42.143Z | observation_span_recorded |  |  |  |
| 29293 | 2026-08-25T07:31:42.248Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 29294 | 2026-08-25T07:32:24.945Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 29295 | 2026-08-25T07:32:25.078Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 29296 | 2026-08-25T07:32:25.195Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 29297 | 2026-08-25T07:32:25.318Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 29298 | 2026-08-25T07:32:25.437Z | state_transition | READY | ROUTED | reason=route_selected |
| 29299 | 2026-08-25T07:32:25.568Z | observation_span_recorded |  |  |  |
| 29300 | 2026-08-25T07:32:26.265Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8827d8c2195b4c08b17f10e014743a84 |
| 29301 | 2026-08-25T07:32:26.382Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 29302 | 2026-08-25T07:32:27.087Z | observation_span_recorded |  |  |  |
| 29303 | 2026-08-25T07:32:27.365Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8827d8c2195b4c08b17f10e014743a84 |
| 29304 | 2026-08-25T07:32:27.480Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 29305 | 2026-08-25T07:32:28.151Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:de487489d6655339; input_fingerprint=f0ff2795c9167885df754bae68904c80e0769d7750c321ea91c745f57509b9e0 |
| 29306 | 2026-08-25T07:32:28.405Z | managed_process_admitted |  |  | owner=default |
| 29307 | 2026-08-25T07:32:28.646Z | managed_process_started |  |  | owner=default |
| 29308 | 2026-08-25T07:32:30.797Z | managed_process_terminal |  |  | owner=default |
| 29309 | 2026-08-25T07:32:31.013Z | proof_recorded |  |  | stage_id=check:de487489d6655339; status=passed; cache_hit=False; input_fingerprint=f0ff2795c9167885df754bae68904c80e0769d7750c321ea91c745f57509b9e0 |
| 29310 | 2026-08-25T07:32:31.226Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2be094743bdf8724; input_fingerprint=8d7afac36ad4acfa946303e01e27540eb8c16e8da1300fcda6b11aaf8d4384c8 |
| 29311 | 2026-08-25T07:32:31.462Z | managed_process_admitted |  |  | owner=default |
| 29312 | 2026-08-25T07:32:31.604Z | managed_process_started |  |  | owner=default |
| 29313 | 2026-08-25T07:32:31.964Z | managed_process_terminal |  |  | owner=default |
| 29314 | 2026-08-25T07:32:32.222Z | proof_recorded |  |  | stage_id=check:2be094743bdf8724; status=passed; cache_hit=False; input_fingerprint=8d7afac36ad4acfa946303e01e27540eb8c16e8da1300fcda6b11aaf8d4384c8 |
| 29315 | 2026-08-25T07:32:32.346Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6e26545342b091f0; input_fingerprint=95ea80818f91eb356045e58cbc891233e0335637057b8a485371da8e53373079 |
| 29316 | 2026-08-25T07:32:32.621Z | managed_process_admitted |  |  | owner=default |
| 29317 | 2026-08-25T07:32:32.836Z | managed_process_started |  |  | owner=default |
| 29318 | 2026-08-25T07:32:33.144Z | managed_process_terminal |  |  | owner=default |
| 29319 | 2026-08-25T07:32:33.344Z | proof_recorded |  |  | stage_id=check:6e26545342b091f0; status=passed; cache_hit=False; input_fingerprint=95ea80818f91eb356045e58cbc891233e0335637057b8a485371da8e53373079 |
| 29320 | 2026-08-25T07:32:33.478Z | proof_cache_miss |  |  | reason=cold; stage_id=check:12a2a7ea4715cef9; input_fingerprint=d006bc9ca98c151993ef07103da76cfaa713f993d78da7509ad4a49cecd304e3 |
| 29321 | 2026-08-25T07:32:33.756Z | managed_process_admitted |  |  | owner=default |
| 29322 | 2026-08-25T07:32:33.962Z | managed_process_started |  |  | owner=default |
| 29323 | 2026-08-25T07:32:34.364Z | managed_process_terminal |  |  | owner=default |
| 29324 | 2026-08-25T07:32:34.665Z | proof_recorded |  |  | stage_id=check:12a2a7ea4715cef9; status=passed; cache_hit=False; input_fingerprint=d006bc9ca98c151993ef07103da76cfaa713f993d78da7509ad4a49cecd304e3 |
| 29325 | 2026-08-25T07:32:34.811Z | observation_span_recorded |  |  |  |
| 29326 | 2026-08-25T07:32:34.929Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 29327 | 2026-08-25T07:33:38.036Z | quality_outcome_recorded |  |  |  |
| 29328 | 2026-08-25T07:33:38.196Z | observation_span_recorded |  |  |  |
| 29329 | 2026-08-25T07:33:38.300Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 29330 | 2026-08-25T07:33:38.602Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:de487489d6655339 | passed | f0ff2795c9167885df754bae68904c80e0769d7750c321ea91c745f57509b9e0 | False | 2644 | 0 |
| check:2be094743bdf8724 | passed | 8d7afac36ad4acfa946303e01e27540eb8c16e8da1300fcda6b11aaf8d4384c8 | False | 751 | 0 |
| check:6e26545342b091f0 | passed | 95ea80818f91eb356045e58cbc891233e0335637057b8a485371da8e53373079 | False | 766 | 0 |
| check:12a2a7ea4715cef9 | passed | d006bc9ca98c151993ef07103da76cfaa713f993d78da7509ad4a49cecd304e3 | False | 880 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1583136a00c64c76befd40a90915f473 | accepted | 026f79b3ab5997cb15f38a3b41769da6a79d790b | 6482937c30a1658ad92fc41836c46ac2dd773e193b2bbcbad6b49045303d6814 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `41`
- Chain head: `f85e09493e466978b7c1c21e6a81cc7d2634f73b58dff0f83dcfff6968ac9cf6`
