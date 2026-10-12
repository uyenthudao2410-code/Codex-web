# r10 + Store395 authority preparation — pending combined approval

The primary helper for the combined rollout is `ubuntu-r10-store-authority-v2-pinned.py`, SHA256 `ab182f47b605e5edac1e30cb9cdf48ca53a571f0cbb5367a0f6fb837cbe0c9af`. Its manifest is `r10-authority-helper-v2-pinned-manifest.json`. Earlier prepared helpers and the fixed 19:19 deadline helper remain immutable evidence.

## Exact target and source

- Server/user/service: `svhome@100.116.112.22`, user `codex-control-plane.service`.
- Required source snapshot: `395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5`.
- Required package fingerprint: `sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419`.
- Binding: `bind_3e05bf64cb3e4bab93d930ae1692bebb`.
- Device: `72ceec2d-e3f2-472f-8e3c-99fffe053035`.
- Workspace/generation: `workspace_dda1d78e9a21402aa6213f72af64f788` / `generation_c2f13e8d02344cf6a38a3f42ecfa59b6`.
- Existing grant remains `mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd`; its complete private digest must agree with the original r9 owner-operation marker.

The helper verifies the registered Tools-Codex-web target and exact declared Read/Edit/Exec capabilities. It does not modify standing file/exec policies, service grant scopes, server exec configuration or Windows policy installers. It never deploys, restarts, executes a standalone Sandbox probe, replays a command, restores SQLite, issues SQL data writes, or accepts the pending local RUN.

## Execution sequence after separate approval

1. Deploy the immutable Store packet. Its deployment helper expects the original scoped pilot, closes intake and ends in `recovery` on the new service instance.
2. Run the primary authority helper in `observe`. Pin the new service instance and quiescent state digest.
3. Run `close --operator-approved --execute` with those pins and the fresh current r9 epoch `activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7`. This creates one protected operation marker; the already closed recovery intake remains closed.
4. Run `renew --operator-approved --execute` with the same pins and fresh r9 epoch. The first approved renewal anchors `requested_at_ms` once, persists exactly `expires_at_ms = requested_at_ms + 3600000`, closes only the prior owner context, and creates one exact-target context and pilot through supported owner APIs. A retry cannot extend this window. Response loss is recovered by observing the exact same-expiry context/pilot before continuing.
5. Activate r10 and sync the compact metadata assignment to the local runtime using the controller's separate guarded activation operation.
6. Observe again, then run `reopen --operator-approved --execute` with the new service/state pins and the freshly observed r10 epoch. The epoch must differ from the predecessor and agree with the node heartbeat. The node must be ready, local policy enabled and non-expired. Only `scoped_pilot` can reopen.

All actions, work requests, delivery attempts, receipts, reconciliations, task sessions, writer leases, acceptances and intent rows are privately hashed and must stay identical throughout the authority operation. The original 13 historical/quarantined families must retain digest `825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed`. Context/pilot rows are changed only through the named owner APIs; settled r9 canary records remain unchanged.

The protected marker directory is `/home/svhome/.local/state/codex-control-plane/owner-operations/r10-store395-60m-v2-pinned`. Marker ownership/mode, exclusive owner lock, service identity and data fingerprints guard retries. A changed marker, expired anchored window, concurrent state change or wrong node epoch stops the operation without an automatic wider grant or renewed deadline.

## Receipt schema for the local activation guard

No real mutation receipts exist yet. The controller chooses their local evidence filenames after approved execution.

Read-only observation emits `phase = r10_store_read_only_preflight`, `source_revision`, `package_source_sha256`, `service_instance_id`, `admission`, `state`, `state_sha256`, `binding_id`, grant identity/scopes and node policy/heartbeat/activation fields.

Closure and renewal retain the existing r9 receipt schema:

- `phase = intake_closed` or `same_scope_renewal_complete`, `ok = true`, `remote_mutation = true`.
- Exact source, host, service, service instance, binding and `admission = recovery`.
- `state` includes the original historical digest, patch acceptance digest and new `all_action_task_intent_families_sha256`.
- `service_restart = false`, `ubuntu_code_deployed = false`, `service_grant_changed = false`.
- Renewal includes `requested_at_ms`, `expires_at_ms`, context/pilot IDs, `duration_ms = 3600000`, and exact `policy_assignment` device/workspace/generation/context/expiry. These fields are null before renewal.
- `activation_epoch` remains null before reopening; the read-only preflight proves the r9 predecessor epoch used for closure/renewal.

The local activation guard should require the same source, service instance and protected state across observation, closure and renewal, and compare the exact policy assignment. It should not require a future r10 epoch in pre-activation receipts.

## Prepared proof and approval boundary

The helper is frozen from the immutable original r9 routines and Store packet manifest, with explicit new source pins. It has no dependency on later checkout or candidate source changes. Syntax/hash/API-route verification passed. Five local negative cases exercised its actual main guard using synthetic read-only observations: missing operator approval, wrong service, wrong predecessor epoch, stale predecessor heartbeat and attempting to reopen r9 were all rejected before the mutation boundary. This is preparation proof, not live authority or runtime proof.

AGENTS.md §5 requires the user's combined approval naming r10 activation, this Store snapshot/server/service operation, intake transition and exactly one same-scope 60-minute authority window. No remote operation was performed while preparing these artifacts.
