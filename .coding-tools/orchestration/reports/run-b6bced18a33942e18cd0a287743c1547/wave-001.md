# Orchestration Wave 1

- Run: `b6bced18a33942e18cd0a287743c1547`
- Wave: `4f38d165be614d7b9ea9d01bcdf5ec7e`
- Objective: Fix the demonstrated Windows artifact-to-npm smoke failure without weakening the production prepack/release-manifest guard. The smoke currently creates only a local file:// manifest in %TEMP% and then runs npm pack directly in npm/webcodex, whose prepack requires a publish-ready canonical manifest. Change only scripts/npm_install_windows_smoke.ps1 so it creates two manifests from the same real artifact SHA: (1) canonical GitHub release URL manifest staged into a tracked-source-only temporary npm package tree for release-manifest validation and npm pack, and (2) the existing local file:// manifest used only via WEBCODEX_MANIFEST for the offline installer. Stage package sources from the exact current commit with git archive, not by copying the workstation tree. Preserve the strict prepack check and all existing installer assertions/cleanup. Do not touch unrelated files.
- Mode: `mcp_only`
- Base HEAD: `bb8ccdcb87a13afc4c4d3a99b756cf821dfcfe72`
- Worktree fingerprint: `c45674a4f0be82f7d296b0145f5a1ef81a0b3de88e1d2427923b01974e4019eb`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 475 | 2026-08-13T17:55:17.582Z | run_started |  | PREFLIGHT |  |
| 476 | 2026-08-13T17:55:17.957Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 477 | 2026-08-13T17:55:18.133Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 478 | 2026-08-13T17:55:18.228Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 479 | 2026-08-13T17:55:18.320Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 480 | 2026-08-13T17:55:18.411Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 481 | 2026-08-13T17:55:18.520Z | state_transition | READY | ROUTED | reason=route_selected |
| 482 | 2026-08-13T17:55:18.847Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7c05827e309d46ce8cfb970430c88fbb |
| 483 | 2026-08-13T17:55:18.947Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 484 | 2026-08-13T17:55:19.342Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7c05827e309d46ce8cfb970430c88fbb |
| 485 | 2026-08-13T17:55:19.419Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 486 | 2026-08-13T17:55:20.158Z | proof_recorded |  |  | stage_id=check:aa6d51931ad29c1c; status=passed; cache_hit=False; input_fingerprint=a7bb18604230a46126af799239b20bd40fedf41699f6610b97624c75a8c7a1de |
| 487 | 2026-08-13T17:55:20.601Z | proof_recorded |  |  | stage_id=check:cc3d982ea1184aa2; status=passed; cache_hit=False; input_fingerprint=39b6f3a9c1dafd284711c2157fc0758dd5aabdccacf74fb92969c507a6570c70 |
| 488 | 2026-08-13T17:55:24.792Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ee536a5e9589fb10568968ca30e25cb5e8e4e35a01a5cff559fff36e4ee31358 |
| 489 | 2026-08-13T17:55:25.032Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:aa6d51931ad29c1c | passed | a7bb18604230a46126af799239b20bd40fedf41699f6610b97624c75a8c7a1de | False | 368 | 0 |
| check:cc3d982ea1184aa2 | passed | 39b6f3a9c1dafd284711c2157fc0758dd5aabdccacf74fb92969c507a6570c70 | False | 90 | 0 |
| verify:tests | passed | ee536a5e9589fb10568968ca30e25cb5e8e4e35a01a5cff559fff36e4ee31358 | False | 3984 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `55a482306321f69b503faae50080c0c627c3da5b790917ffbb23cbf0815f84f7`
