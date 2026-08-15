# Orchestration Wave 2

- Run: `edd43e17f28a4a6eaf96b3ec5109ff5e`
- Wave: `9453bd0b9f2f4bedac3aeb8b25632c4d`
- Objective: Close the controlled-replay causal-acceptance gap without adding a public tool or inferring success from process exit code. After each isolated trial command, read that trial workspace's authoritative EOCL orchestration ledger and attest exactly one accepted run whose evaluation/source identity matches the trial manifest. Require an accepted checkpoint plus proof/oracle evidence, and fail closed on missing, ambiguous, identity-mismatched, or route-policy-mismatched evidence. Preserve existing plan-only and no-ledger behavior.
- Mode: `mcp_only`
- Base HEAD: `f64abe25a85e6abaa9fe9eeacd3665eb29a82515`
- Worktree fingerprint: `32eab4044dd67ff1fa7c4c1e188a7c1bacf61eba3e7f482edd455db82845661d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 5317 | 2026-08-15T11:00:22.657Z | wave_replanned |  | PREFLIGHT | reason=Acceptance review found that individual EOCL acceptance is insufficient for a paired study unless both policies in each pair share the exact EOCL pair_fingerprint, which includes source/worktree and task/oracle identity. Add that explicit pair-level equality gate and a focused fail-closed test; do not change the ledger attestation design. |
| 5318 | 2026-08-15T11:00:22.871Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 5319 | 2026-08-15T11:00:23.065Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5320 | 2026-08-15T11:00:23.286Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 5321 | 2026-08-15T11:00:23.526Z | state_transition | READY | ROUTED | reason=route_selected |
| 5322 | 2026-08-15T11:00:24.156Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7f2b0824844c404baa7cb5087c63298e |
| 5323 | 2026-08-15T11:00:24.511Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 5324 | 2026-08-15T11:00:25.267Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7f2b0824844c404baa7cb5087c63298e |
| 5325 | 2026-08-15T11:00:25.468Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 5326 | 2026-08-15T11:00:26.008Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=8b5480b3f12451af2978a7e412b9a8c0d71a5e95eaf6eacfb3c71a973c942cdc |
| 5327 | 2026-08-15T11:00:43.164Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=8b5480b3f12451af2978a7e412b9a8c0d71a5e95eaf6eacfb3c71a973c942cdc |
| 5328 | 2026-08-15T11:00:43.916Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5329 | 2026-08-15T11:03:14.489Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 8b5480b3f12451af2978a7e412b9a8c0d71a5e95eaf6eacfb3c71a973c942cdc | False | 16765 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 068be57f95824fa79743bf29f89e8d04 | accepted | f64abe25a85e6abaa9fe9eeacd3665eb29a82515 | 84c78116455abe2291bb193b9efbd39bd8ee412a219961eaecb406752f7732f2 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `09bd841cd548ef4572bdf28648655b8d06706288e630c26cd721057845fc55c0`
