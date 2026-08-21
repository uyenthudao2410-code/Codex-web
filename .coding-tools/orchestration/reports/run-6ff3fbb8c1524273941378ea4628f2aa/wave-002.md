# Orchestration Wave 2

- Run: `6ff3fbb8c1524273941378ea4628f2aa`
- Wave: `fbfedf3da6c14438b349131d215f2c07`
- Objective: Build and verify the final local NSIS release-candidate artifact from the already accepted source fingerprint. Run the complete dist script, re-run packaged Recovery smoke against the final win-unpacked output, verify git diff/source-root hygiene, and print content-free installer SHA-256, size, and mtime. Local verification only: no release/publish/deploy, no commit/push, no live runtime restart, no provider dispatch.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `cae7694780453fd0ca2fa28930eb916ba245fa23e09666d2e3452811354e9050`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25921 | 2026-08-21T04:30:59.207Z | wave_replanned |  | PREFLIGHT | reason=The final NSIS evidence wave exposed a genuine provenance/isolation defect: unrelated commands from another conversation were automatically bound to the active Coding Web run/wave. Before re-proving package/hash, fix this cross-session ownership contamination. This is a changed strategy and scope directly required to make final acceptance trustworthy; do not retry the contaminated proof unchanged. |
| 25922 | 2026-08-21T04:31:00.388Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25923 | 2026-08-21T04:32:04.990Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25924 | 2026-08-21T04:32:19.058Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25925 | 2026-08-21T04:33:34.378Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25926 | 2026-08-21T04:34:42.311Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25927 | 2026-08-21T04:34:43.126Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25928 | 2026-08-21T04:34:43.858Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 25929 | 2026-08-21T04:34:44.641Z | state_transition | READY | ROUTED | reason=route_selected |
| 25930 | 2026-08-21T04:34:47.014Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a1bf5bc951584d3397493d54ace8b24b |
| 25931 | 2026-08-21T04:34:47.481Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25932 | 2026-08-21T04:34:49.147Z | patch_surface_observed |  |  |  |
| 25933 | 2026-08-21T04:34:49.518Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a1bf5bc951584d3397493d54ace8b24b |
| 25934 | 2026-08-21T04:34:49.783Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 25935 | 2026-08-21T04:34:50.322Z | proof_cache_miss |  |  | reason=cold; stage_id=check:07e3330b5c5b0b74; input_fingerprint=b70cb1554cce550018924d0d0a1756ad20a669a050a49e1d631cb280ed868286 |
| 25936 | 2026-08-21T04:34:50.961Z | managed_process_admitted |  |  | owner=default |
| 25937 | 2026-08-21T04:34:51.485Z | managed_process_started |  |  | owner=default |
| 25938 | 2026-08-21T04:35:12.532Z | managed_process_terminal |  |  | owner=default |
| 25939 | 2026-08-21T04:35:13.472Z | proof_recorded |  |  | stage_id=check:07e3330b5c5b0b74; status=failed; cache_hit=False; input_fingerprint=b70cb1554cce550018924d0d0a1756ad20a669a050a49e1d631cb280ed868286 |
| 25940 | 2026-08-21T04:35:13.920Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 25941 | 2026-08-21T04:35:14.277Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 25942 | 2026-08-21T04:35:14.617Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:07e3330b5c5b0b74 | failed | b70cb1554cce550018924d0d0a1756ad20a669a050a49e1d631cb280ed868286 | False | 22461 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `86`
- Chain head: `c279f696ad227144f73aa3f55d5e2582310ef2d2b424f06a2cdf03a5c8d3ff25`
