# Orchestration Wave 2

- Run: `36b6631db5944c29b23b455d0f9b0795`
- Wave: `8133f1e17b504438b87b1565a03d9727`
- Objective: Fix the live Phase 3A Install runtime failure without changing supervisor policy. Normalize every custom PowerShell helper invocation that uses method-like `FunctionName(...)` syntax into idiomatic command syntax with a separating space/parenthesized argument, especially Assert-Manifest, Test-AbsoluteSafePath, Test-PathEqual, Get-Sha256File, and Get-Sha256Text in Install/Status/Uninstall/Run paths. Add a static regression to reject method-like calls for those helpers. Preserve all fail-closed health/restart behavior and unrelated runtime evidence. Prove PowerShell AST parse, focused supervisor tests, and full npm test.
- Mode: `mcp_only`
- Base HEAD: `6299c052567852607ddcda30fabe48c859eef932`
- Worktree fingerprint: `25402d5abb7e1ead012b327eb0ff1ee549f47ad4549c5a0e75b83571476cdc79`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6421 | 2026-08-16T08:45:58.041Z | wave_replanned |  | PREFLIGHT | reason=The new helper-call regression falsely matched legitimate declarations such as `function Get-Sha256File(...)`. Filter declaration lines before applying the method-like call regex; keep the production helper-call normalization unchanged. |
| 6422 | 2026-08-16T08:45:58.159Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6423 | 2026-08-16T08:45:58.266Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6424 | 2026-08-16T08:45:58.406Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6425 | 2026-08-16T08:45:58.507Z | state_transition | READY | ROUTED | reason=route_selected |
| 6426 | 2026-08-16T08:45:58.932Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=21bf8c23befc48ea95a3834a79c9d571 |
| 6427 | 2026-08-16T08:45:59.073Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6428 | 2026-08-16T08:45:59.573Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=21bf8c23befc48ea95a3834a79c9d571 |
| 6429 | 2026-08-16T08:45:59.703Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6430 | 2026-08-16T08:46:00.055Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d9c099758f2ff7c2; input_fingerprint=fab49c237f34cdadf48bcb79b2b3842ca12eaa4ab1dd434ddc0e54d484318787 |
| 6431 | 2026-08-16T08:46:00.331Z | managed_process_admitted |  |  | owner=default |
| 6432 | 2026-08-16T08:46:00.576Z | managed_process_started |  |  | owner=default |
| 6433 | 2026-08-16T08:46:01.148Z | managed_process_terminal |  |  | owner=default |
| 6434 | 2026-08-16T08:46:01.418Z | proof_recorded |  |  | stage_id=check:d9c099758f2ff7c2; status=passed; cache_hit=False; input_fingerprint=fab49c237f34cdadf48bcb79b2b3842ca12eaa4ab1dd434ddc0e54d484318787 |
| 6435 | 2026-08-16T08:46:01.576Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=c6aac298dfcd569744bf1f5c03226297b550bec51d5ace15db2ebdaa12d26706 |
| 6436 | 2026-08-16T08:46:01.860Z | managed_process_admitted |  |  | owner=default |
| 6437 | 2026-08-16T08:46:02.098Z | managed_process_started |  |  | owner=default |
| 6438 | 2026-08-16T08:46:04.731Z | managed_process_terminal |  |  | owner=default |
| 6439 | 2026-08-16T08:46:05.016Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=passed; cache_hit=False; input_fingerprint=c6aac298dfcd569744bf1f5c03226297b550bec51d5ace15db2ebdaa12d26706 |
| 6440 | 2026-08-16T08:46:05.161Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:328e123c63857fd8; input_fingerprint=82568880b123d1eab0c1b3e4f22b88089354fb3371ed4920e45fb43b41932163 |
| 6441 | 2026-08-16T08:46:05.490Z | managed_process_admitted |  |  | owner=default |
| 6442 | 2026-08-16T08:46:05.757Z | managed_process_started |  |  | owner=default |
| 6443 | 2026-08-16T08:46:16.170Z | managed_process_terminal |  |  | owner=default |
| 6444 | 2026-08-16T08:46:16.454Z | proof_recorded |  |  | stage_id=check:328e123c63857fd8; status=passed; cache_hit=False; input_fingerprint=82568880b123d1eab0c1b3e4f22b88089354fb3371ed4920e45fb43b41932163 |
| 6445 | 2026-08-16T08:46:16.617Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=dcf039a17a67e2e6c9518f2b08fbb554d29f24e21e03f62adfb1162ae8c97813 |
| 6446 | 2026-08-16T08:46:16.960Z | managed_process_admitted |  |  | owner=default |
| 6447 | 2026-08-16T08:46:17.202Z | managed_process_started |  |  | owner=default |
| 6448 | 2026-08-16T08:46:27.808Z | managed_process_terminal |  |  | owner=default |
| 6449 | 2026-08-16T08:46:28.072Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=dcf039a17a67e2e6c9518f2b08fbb554d29f24e21e03f62adfb1162ae8c97813 |
| 6450 | 2026-08-16T08:46:28.496Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6451 | 2026-08-16T08:46:38.673Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 6452 | 2026-08-16T08:46:39.006Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d9c099758f2ff7c2 | passed | fab49c237f34cdadf48bcb79b2b3842ca12eaa4ab1dd434ddc0e54d484318787 | False | 1118 | 0 |
| check:fe3ffbf7aa7a92a6 | passed | c6aac298dfcd569744bf1f5c03226297b550bec51d5ace15db2ebdaa12d26706 | False | 3169 | 0 |
| check:328e123c63857fd8 | passed | 82568880b123d1eab0c1b3e4f22b88089354fb3371ed4920e45fb43b41932163 | False | 11007 | 0 |
| verify:tests | passed | dcf039a17a67e2e6c9518f2b08fbb554d29f24e21e03f62adfb1162ae8c97813 | False | 11188 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 0de6f456f3534ca09280c30ac619b67b | accepted | 6299c052567852607ddcda30fabe48c859eef932 | 63e14582429307ac08bae5e398df495297924fabc9e64fb3a6821bb048dcdd31 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `96ad1d8eab742b569bd4899cd59cb5ff1f3ef0cb65eff7c936c9ef9dcaf2e0c0`
