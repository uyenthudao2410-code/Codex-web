# Orchestration Wave 1

- Run: `10147ddcac554c2ba3be22c7bd70f59f`
- Wave: `a5f72a72b96545e280bff521cea30f2e`
- Objective: Correct P0.2 artifact-retention drift with one explicit, provenance-recorded final rebuild. The previously accepted final artifact run 59b40e0a67694ad59385227f6dcfc4d4 is CHECKPOINTED, but its installer bytes SHA256 36E51E2E...F2F38D are no longer retained at dist; current dist contains an older artifact AC923D81...F1DC1. Proven evidence shows accepted RC base 1516f0e5ebcf4086376bb5d144c5e70bbfcf383b -> current HEAD db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc changes only orchestration state/reports and the dated research plan, with no product/package source changes, and there is no second retained copy of the accepted installer. Prepare an explicit corrective `npm run dist` at current product-equivalent HEAD, preserving unrelated dirty evidence files. Verify package config excludes orchestration/docs evidence from packaged product semantics or otherwise account for it. Do not publish/upload, do not install, do not start P0.3, and do not update docs until the rebuilt artifact bytes are hashed and accepted. Acceptance for this build subwave: npm run dist exit 0, installer/blockmap/latest.yml generated non-empty, no product source modified by build, exact base/source identity recorded, no hidden build claim.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `a66fcbd249744d211a29486393c6edaea09b58ef041a720131fa437d983832dd`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14189 | 2026-08-17T14:15:00.667Z | run_started |  | PREFLIGHT |  |
| 14190 | 2026-08-17T14:15:05.952Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14191 | 2026-08-17T14:15:24.255Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 14192 | 2026-08-17T14:15:24.358Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 14193 | 2026-08-17T14:15:24.462Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 14194 | 2026-08-17T14:15:24.565Z | state_transition | READY | ROUTED | reason=route_selected |
| 14195 | 2026-08-17T14:15:25.127Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=952d23d546924442a2a914f51f7b7994 |
| 14196 | 2026-08-17T14:15:25.250Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 14197 | 2026-08-17T14:15:25.802Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=952d23d546924442a2a914f51f7b7994 |
| 14198 | 2026-08-17T14:15:25.907Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 14199 | 2026-08-17T14:15:26.433Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:build; input_fingerprint=607a555dc759eefa7d46bc56f809d9a04f6ba40a044b3352b42aa3b6e3a0a4cc |
| 14200 | 2026-08-17T14:15:26.700Z | managed_process_admitted |  |  | owner=default |
| 14201 | 2026-08-17T14:15:26.942Z | managed_process_started |  |  | owner=default |
| 14202 | 2026-08-17T14:15:50.041Z | managed_process_terminal |  |  | owner=default |
| 14203 | 2026-08-17T14:15:50.265Z | proof_recorded |  |  | stage_id=verify:build; status=failed; cache_hit=False; input_fingerprint=607a555dc759eefa7d46bc56f809d9a04f6ba40a044b3352b42aa3b6e3a0a4cc |
| 14204 | 2026-08-17T14:15:50.375Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 14205 | 2026-08-17T14:15:50.483Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 14206 | 2026-08-17T14:15:50.597Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:build | failed | 607a555dc759eefa7d46bc56f809d9a04f6ba40a044b3352b42aa3b6e3a0a4cc | False | 23594 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `6cacc31020cdee7e851adf565f4f9ce8bda64dc2f0fa2a750cd888ad46b211e3`
