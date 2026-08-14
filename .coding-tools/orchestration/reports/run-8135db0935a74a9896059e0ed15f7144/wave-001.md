# Orchestration Wave 1

- Run: `8135db0935a74a9896059e0ed15f7144`
- Wave: `e8f6986797a347e8b621f1fb1709c892`
- Objective: Remove the remaining OpenCode Provider Adapter process-pipe ResourceWarning observed in the final cross-cutting audit. Close owned stdout/stderr pipe handles after reader threads finish and the provider process is terminal, without changing dispatch semantics, correlation, output parsing, timeout/cancel behavior, public tools, routing, UI, settings, or service state. Add/adjust focused proof so the adapter fake-process test suite runs without ResourceWarning. Do not restart services, run real provider inference, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `7609297462713beb104e5c933ea4d6bf3b24ec11`
- Worktree fingerprint: `826c5d8c5078e0217718d6f6082773a7f1fc010628fa5b27bee2aa4baa10fd6b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1900 | 2026-08-14T10:06:12.249Z | run_started |  | PREFLIGHT |  |
| 1901 | 2026-08-14T10:06:13.056Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1902 | 2026-08-14T10:06:13.245Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1903 | 2026-08-14T10:06:13.454Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1904 | 2026-08-14T10:06:13.653Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1905 | 2026-08-14T10:06:13.862Z | state_transition | READY | ROUTED | reason=route_selected |
| 1906 | 2026-08-14T10:06:14.409Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=185202aa8fc2485d9e89053d459fa7d3 |
| 1907 | 2026-08-14T10:06:14.616Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1908 | 2026-08-14T10:06:15.259Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=185202aa8fc2485d9e89053d459fa7d3 |
| 1909 | 2026-08-14T10:06:15.475Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1910 | 2026-08-14T10:06:17.075Z | proof_recorded |  |  | stage_id=check:a294a087e3ab1ecc; status=passed; cache_hit=False; input_fingerprint=5c128cad091e111ea4960002622955169b3afcdedc37672b633a85fcdef2833f |
| 1911 | 2026-08-14T10:06:24.116Z | proof_recorded |  |  | stage_id=check:d68f99d3d141b6d7; status=passed; cache_hit=False; input_fingerprint=d0f51fd4cb9a2d439054575ff25b562d723c1932fc11f2b0b39aa09fd77b1012 |
| 1912 | 2026-08-14T10:06:24.583Z | proof_recorded |  |  | stage_id=check:3757086afd1e0527; status=passed; cache_hit=False; input_fingerprint=34d8cfc0f5c380ff8d0e54b6634b111e3c2d2540db1039e75ffa8cb9d93fd7c5 |
| 1913 | 2026-08-14T10:06:31.864Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1914 | 2026-08-14T10:07:55.590Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a294a087e3ab1ecc | passed | 5c128cad091e111ea4960002622955169b3afcdedc37672b633a85fcdef2833f | False | 947 | 0 |
| check:d68f99d3d141b6d7 | passed | d0f51fd4cb9a2d439054575ff25b562d723c1932fc11f2b0b39aa09fd77b1012 | False | 6634 | 0 |
| check:3757086afd1e0527 | passed | 34d8cfc0f5c380ff8d0e54b6634b111e3c2d2540db1039e75ffa8cb9d93fd7c5 | False | 115 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 8e085ad099c443b385f969f7b0762e36 | accepted | 7609297462713beb104e5c933ea4d6bf3b24ec11 | 4342ed555b0a358ca2179119219f848ef87265f988ffd0776edd498d1b4bcf6e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `8f941d26f47a3ee7a4e82ca7e15c08a6ec73423b64fbde33f1ca72bae9f68f29`
