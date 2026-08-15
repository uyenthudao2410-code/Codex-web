# Orchestration Wave 2

- Run: `00a856ea608b4cc8af26fe57c934cd18`
- Wave: `8b22231edcfc4e089ba17715e70cfc29`
- Objective: Integrated exact-worktree acceptance proof before live runtime activation. Do not mutate source. Run the full Python MCP regression, root Node/Electron tests, git diff whitespace validation, and conflict check on the current dirty worktree. Do not call providers/reviewers, do not restart inside this proof wave, and preserve all unrelated dirty files.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `ae09845a353ee8ddb342319c62d19d9e22d8a7464ae1182bc28d7e612ba905dc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4532 | 2026-08-15T05:52:06.778Z | wave_replanned |  | PREFLIGHT | reason=The prior proof wave was rejected before test execution because its command used 'cd ../..', which the MCP path validator correctly classified as a filesystem escape. Run the same oracle entirely from the repository root by setting PYTHONPATH to resources/coding-tools-mcp; no source or acceptance-policy change is needed. |
| 4533 | 2026-08-15T05:52:06.961Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4534 | 2026-08-15T05:52:07.165Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4535 | 2026-08-15T05:52:07.516Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4536 | 2026-08-15T05:52:07.690Z | state_transition | READY | ROUTED | reason=route_selected |
| 4537 | 2026-08-15T05:52:08.337Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2c01b42011ff49969dd22d757266414b |
| 4538 | 2026-08-15T05:52:08.522Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4539 | 2026-08-15T05:52:09.156Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2c01b42011ff49969dd22d757266414b |
| 4540 | 2026-08-15T05:52:09.383Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4541 | 2026-08-15T05:52:09.930Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=e12df4bcf16e669d7f952df86700b48ce80f8d47b04d003edacf37ee9e7f9a4d |
| 4542 | 2026-08-15T05:54:05.283Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=e12df4bcf16e669d7f952df86700b48ce80f8d47b04d003edacf37ee9e7f9a4d |
| 4543 | 2026-08-15T05:54:05.451Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4544 | 2026-08-15T05:54:05.617Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | e12df4bcf16e669d7f952df86700b48ce80f8d47b04d003edacf37ee9e7f9a4d | False | 114983 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `bc5caa8f4fa786f393f91059ea6faeafddf1bc0de19da96843dea5cc51f0e396`
