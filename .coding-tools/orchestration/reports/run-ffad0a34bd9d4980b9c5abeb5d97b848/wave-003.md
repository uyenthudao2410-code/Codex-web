# Orchestration Wave 3

- Run: `ffad0a34bd9d4980b9c5abeb5d97b848`
- Wave: `d59f355338ca431a83622b410ba1c4db`
- Objective: P-MP2 integration: connect the already-proven standalone read-only OpenCode Provider Adapter into Execution Hub without changing the Smart-v3 public 8-tool contract or routing thresholds. Add explicit adapter correlation IDs from child env through the existing OpenCode telemetry plugin and Electron strict gateway; correlate telemetry to the adapter delegation even if telemetry races CLI stdout. Make canonical UsageEvent recording idempotent so late measured terminal telemetry attaches exactly once after adapter lifecycle terminalization. Instantiate/cancel the adapter with Runtime lifecycle and block workspace switches while an adapter dispatch is active. Add supervisor-only internal /__control/hub provider_dispatch/provider_observe/provider_cancel actions bound fail-closed to the current task-projected active wave for dispatch, while observation/cancellation can truthfully finish an existing dispatch. Persist only prompt hash/bytes, bounded counts/timing/error class and exact model/dispatch/session IDs; never raw prompt or provider result text. Keep OpenCode worker-only, no controller transfer. Prove with fake provider and focused Node/Python tests only; no real provider/network inference, no UI, restart, settings, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `66739d14834e380dbe9974f20d6e351bfa61a472fd9cbac049c0d39efa856fea`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1828 | 2026-08-14T09:54:41.241Z | wave_replanned |  | PREFLIGHT | reason=The last replan partially applied the intended ledger fix and its regression test, then failed before adapter/server callback changes because an adapter hunk matched five generic lock blocks. Inspection confirms the ledger fix is present and callback changes are absent. Materially continue with uniquely anchored exact method blocks only; do not reapply or alter the already-green gateway/plugin integration. |
| 1829 | 2026-08-14T09:54:41.453Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1830 | 2026-08-14T09:54:41.642Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1831 | 2026-08-14T09:54:41.817Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1832 | 2026-08-14T09:54:41.996Z | state_transition | READY | ROUTED | reason=route_selected |
| 1833 | 2026-08-14T09:54:42.551Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8aec7d7ebea248fea32d1d75fd525ea6 |
| 1834 | 2026-08-14T09:54:42.725Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1835 | 2026-08-14T09:54:43.451Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8aec7d7ebea248fea32d1d75fd525ea6 |
| 1836 | 2026-08-14T09:54:43.642Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1837 | 2026-08-14T09:54:44.558Z | proof_recorded |  |  | stage_id=check:e41767fbf3863758; status=passed; cache_hit=False; input_fingerprint=442892dacd97969307c032c6a73137d274badae2a7d9cbbf61eac8c4394d5cc7 |
| 1838 | 2026-08-14T09:54:45.916Z | proof_recorded |  |  | stage_id=check:94a8a740323528c0; status=passed; cache_hit=False; input_fingerprint=b9cea8b8a2b523326146ac1bb3e3f6ea3c2b6648cf6d0bf56226dd9f8c2d522b |
| 1839 | 2026-08-14T09:54:51.651Z | proof_recorded |  |  | stage_id=check:d68f99d3d141b6d7; status=passed; cache_hit=False; input_fingerprint=bdd9c91448a3446a85117c1ad8c13a54056a85c6469451622664eba8dcef2c47 |
| 1840 | 2026-08-14T09:54:52.841Z | proof_recorded |  |  | stage_id=check:27d05452881c31de; status=passed; cache_hit=False; input_fingerprint=19c3ba0a0958ab004a70b736c435eb7aa3b134c463b8109999f739c823924686 |
| 1841 | 2026-08-14T09:54:53.510Z | proof_recorded |  |  | stage_id=check:cc2f1f958275bce8; status=passed; cache_hit=False; input_fingerprint=5e415c23aeb1fae9e0828790584b8c394b8a685f6f1f84c8a462f2096789bbac |
| 1842 | 2026-08-14T09:54:54.016Z | proof_recorded |  |  | stage_id=check:54dbb34751a387ae; status=passed; cache_hit=False; input_fingerprint=2c323f229fd612e46d281fd71a26f366ccdf471e8fd1ddfff87784de2c2a76f5 |
| 1843 | 2026-08-14T09:54:54.390Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1844 | 2026-08-14T09:56:15.656Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e41767fbf3863758 | passed | 442892dacd97969307c032c6a73137d274badae2a7d9cbbf61eac8c4394d5cc7 | False | 303 | 0 |
| check:94a8a740323528c0 | passed | b9cea8b8a2b523326146ac1bb3e3f6ea3c2b6648cf6d0bf56226dd9f8c2d522b | False | 967 | 0 |
| check:d68f99d3d141b6d7 | passed | bdd9c91448a3446a85117c1ad8c13a54056a85c6469451622664eba8dcef2c47 | False | 5357 | 0 |
| check:27d05452881c31de | passed | 19c3ba0a0958ab004a70b736c435eb7aa3b134c463b8109999f739c823924686 | False | 865 | 0 |
| check:cc2f1f958275bce8 | passed | 5e415c23aeb1fae9e0828790584b8c394b8a685f6f1f84c8a462f2096789bbac | False | 306 | 0 |
| check:54dbb34751a387ae | passed | 2c323f229fd612e46d281fd71a26f366ccdf471e8fd1ddfff87784de2c2a76f5 | False | 170 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 0969e12236c84d05bcc1314d54116b70 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | d370286e94930f9b7437d04cde9424afcaeb1c898c979a9b1fecbb14b8dc7768 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `f2a7663ec986ae9ae472f9f1aec99fa641cc5bad4a6a51a39af7bc4a33f6990f`
