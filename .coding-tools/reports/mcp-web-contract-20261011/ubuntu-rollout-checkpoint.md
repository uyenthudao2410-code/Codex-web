# Ubuntu rollout checkpoint — 2026-10-11

## Result

Authorized revision `beaa9d5ade4926ef231e3ec9d0a517fe93830e90` is active on `svhome@100.116.112.22`, user service `codex-control-plane.service`. Service PID `794023` started at 15:24:40 +07. The current release symlink and live health report the same revision and package fingerprint `sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835`. Release verification passed for all 38 files, schema 28.

The transfer matched archive SHA-256 `e31132a545da55cad564a373c138bb644917c8cbce73e87b724c88dfee6f3b36`. Runtime delta is limited to `mcp_facade.py`, new `mcp_status.py`, `node_agent.py`, and generated `DEPLOYMENT.md`.

## Recovery and preservation

Read-only inspection established that the previous deployment had not begun: revision `70de202d` was active, the candidate archive/release were absent, and no local SSH/SCP helper was active. The exact archive was transferred and checked before the guarded driver ran.

Recoverable configuration and verified SQLite snapshot remain private on Ubuntu at `/home/svhome/.local/state/codex-control-plane/deployment-backups/mcp-web-contract-20261011T082438Z`. Snapshot SHA-256 is `e16364519776be91afdc939d8c96ded895a1ce253115a8aaed84d1a0102c1b78`; SQLite integrity and schema checks passed. The previous immutable release is preserved. No database restore was performed.

Before and after deployment/renewal: 28 actions, 4 task sessions, 1 acceptance, zero queued/accepted actions, zero open writer leases, zero open task sessions. Thirteen historical unresolved actions remain preserved: 12 quarantined UNKNOWN and 1 unobserved dispatch. Their complete row-family digest remained `825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed`. No historical replay, new read, patch, task mutation or local acceptance occurred.

## Same-scope renewal

Admission is `scoped_pilot`. The exact binding `bind_3e05bf64cb3e4bab93d930ae1692bebb` remains unchanged.

- Context: `ctx_80a102323c14412fa539a396a1edd034`.
- Pilot: `pilot_4723468161ec46269ea73e93e854f52a`.
- Approved window: exactly 3,600,000 ms from `1791707184008` to `1791710784008` (15:26:24.008 to 16:26:24.008 +07 on 2026-10-11).
- Device: `72ceec2d-e3f2-472f-8e3c-99fffe053035`.
- Workspace: `workspace_dda1d78e9a21402aa6213f72af64f788`.
- Generation: `generation_c2f13e8d02344cf6a38a3f42ecfa59b6`.
- Existing service grant `mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd` already covers the full window. Its scopes, expiry and credential were preserved without mutation.

The renewal continuation stores a private public-metadata receipt before authority creation. A retry reuses its fixed expiry and uniquely matching live context/pilot rather than creating another 60 minute window. Supported operator API calls closed two expired contexts and created the single new context/pilot; no direct database writes were used.

## Remaining proof and next action

Install the matching local Windows policy and activate the authorized r4 candidate while preserving the local acceptance queue. Then run the prepared MCP inventory, wrong-contract self-correction, historical terminal diagnostic, and fixture read proof. Windows exec readiness remains unproven; this Ubuntu deployment does not establish Sandbox readiness.

Primary Git remains `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`, with existing unrelated work preserved and no primary staging, commit or push. No Windows operation was performed by this workstream. Credentials remained in remote process memory; outputs contain fixed diagnostics, public IDs and hashes only.

## Evidence

- `ubuntu-pre-resume-inspection.jsonl`: baseline identity, read-only registry and historical fence.
- `ubuntu-deployment-preflight.jsonl`: exact archive/baseline/quiescence proof.
- `ubuntu-deployment-result.jsonl`: private backup, switch/restart, health and preservation proof.
- `ubuntu-authority-renewal.jsonl`: exact scope/window, preserved service grant and final admission.
- `ubuntu-inspect-tail.py`, `ubuntu-renew-tail.py`: bounded continuation helpers.

An initial read-only inspection attempted loopback port 8765, while the configured API binds to the Tailscale address. It failed with `CONTROL_PLANE_API_FAILED` before any mutation. The corrected inspection used the configured bind address and passed; this was an inspection helper issue, not a service failure.

## Final observation after Windows activation and live proof

At observation `1791708015669` (15:40:15.669 +07), the same service PID `794023`, service instance, deployed revision, expected/live package fingerprint and 38-file release verification still passed. Node heartbeat age was 12,725 ms; readiness `ready`, policy state `enabled`, and advertised policy expiry remained in the future. Admission remained `scoped_pilot`; the standing context and pilot retained exact expiry `1791710784008` (16:26:24.008 +07).

The two live-proof actions `act_c8412bf197ee427fb9a983ad0bd19ab2` and `act_a600a322c7cc4dbf95c2c66b055820e4` were both `settled` with latest receipt `completed`. Aggregate action count is now 30; task sessions remain 4 and acceptances 1. Queued actions, accepted actions, open writers and open tasks remain zero. The thirteen historical unresolved row families retain the same digest. No final-observation mutation, renewal, restart, deployment or action replay occurred.

The first final helper assertion assumed only the standing context could be live. The facade's two proof reads had created short per-action contexts under the same binding, each bounded within the approved expiry; this caused `FINAL_CONTEXT_CHANGED` in the observer while the live system was healthy. The observer was corrected to verify the exact standing context plus bounded transient contexts. By the succeeding observation the transient contexts had expired and the live-context count was one. Both observations remain in evidence; the final succeeded with `remote_mutations=false`.

Final evidence: `ubuntu-final-observation.jsonl`, `ubuntu-final-identity-inspection.jsonl`, and the read-only helper `ubuntu-final-observe-tail.py`. Exec readiness remains unproven by these read-only observations.
