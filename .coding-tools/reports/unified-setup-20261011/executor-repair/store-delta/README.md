# Store lookup deployment packet — pending approval

Prepared on `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f` against the exact served snapshot `5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f`, not against Git HEAD. No SSH, service, authority, runtime, commit or push operation was performed.

## Immutable source delta

- Candidate source snapshot: `395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5`.
- Package source fingerprint: `sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419`.
- Archive SHA256: `bf76625554e32478202191c29ccdea0790448a47971db30af54a7aa5959d9061`.
- Exactly `control-plane/control_plane/store.py` changes; the other 37 payload files are byte-identical to the served snapshot. Schema remains 28.
- `ControlPlaneStore.assigned_read_only_policy_context` has two diff hunks: explanation and the `NOT EXISTS` query for the six sealed operation-intent families. The remaining Store AST is identical.
- The payload retains the served LF format. Local CRLF source SHA `19f8447286e8ffeab1de854f378e31656206e9c177d3a514beb2ad442dccc537` maps to payload SHA `1d45615fff15e19dc50d4a7cead04b7566ed0acd87489f2ab5cd69adbc24a9e0`.
- The base archive, manifest, every base payload hash and local extracted base are verified before preparation. The frozen release verifier passes on the new 38-file snapshot. No unrelated source delta is included.

The coordinator has reported 6 focused Store tests and 1 existing HTTP assignment/ambiguity test passed on the frozen local source. Those unchanged tests were not rerun here. Local packet preparation validates syntax, full release integrity, source scope, archive/helper hashes and helper API routes; it is not live deployment proof.

## Guarded deployment

`ubuntu-store-rollout.py` defaults to read-only preflight. Execution requires explicit `--execute`, target `100.116.112.22`, the candidate revision and the exact remote archive path. Its fixed target is user `svhome`, user service `codex-control-plane.service`.

It fails before mutation if the baseline source/package, service instance `cp_d203277517b747e4b056ec0184d09709`, current symlink, protected configuration, archive, historical quarantine digest or quiescence changed. It requires zero queued/accepted actions, open tasks and writers, with the original 13 quarantined/historical action families intact.

After separate owner approval, the execution sequence is:

1. Acquire the existing owner deployment lock and close intake through the authenticated recovery endpoint.
2. Create a new private backup directory; copy protected configuration and make an integrity-verified SQLite snapshot.
3. Extract a new immutable release, verify all hashes and the one-file delta, then prepare exact revision/fingerprint configuration.
4. Switch `current`, reload systemd and restart the specified user service once.
5. Require a new service identity and expected health/fingerprint; privately compare hashes of all action, request, receipt, task, writer, acceptance, context and intent rows.

Success leaves admission in `recovery`. The helper does not renew authority, restore SQLite, alter tasks/receipts, replay commands or activate Windows. Failure rolls back code/configuration when exact guards permit, restarts the previous source, verifies the same data families, and leaves intake closed. Protected backup files and database content are never printed. The database snapshot is evidence and recovery material; it is never automatically restored over current state.

## Observe and reopen with the unchanged deadline

`ubuntu-store-observe-reopen.py observe` is read-only and pins the new source snapshot/package. It reports sanitized service, state, node and existing authority identifiers.

`reopen --execute` additionally requires the fresh observed service instance, state digest and expected Windows activation epoch. It preserves:

- Context `ctx_655e717e5c634cc1922d0f0d2e9d33c6`.
- The exact Tools-Codex-web binding/device/workspace/generation and declared Read/Edit/Exec capabilities.
- Grant `mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd`, verified against the original private r9 marker digest.
- Deadline `1791721156518` (19:19:16.518 +07 on 2026-10-11).

The implementation of recovery admission revokes live pilot decisions. Therefore old pilot `pilot_6c6dd3a9b03e4221af64068ff5ea0afd` remains revoked history; it cannot be preserved as a live decision or revived. Creating one replacement decision requires separate owner approval, expressed by `--replace-revoked-pilot`. The replacement retains the old scope and exact deadline. It does not create or extend a context or service grant. Its private marker supports observing a response-loss boundary before continuing, with no duplicate decision or command replay.

Reopen checks source/service identity, unmodified data families, exact existing authority, a fresh ready node, enabled non-expired local policy and the expected activation epoch before opening `scoped_pilot`. If the existing deadline expires, it fails with `AUTHORIZED_WINDOW_EXPIRED_NO_RENEWAL`; a renewal requires another authorized operation and a separately prepared helper.

## Approval boundary and remaining evidence

AGENTS.md §5 requires new explicit approval naming this snapshot, `svhome@100.116.112.22`, the service restart, intake close/reopen and same-deadline pilot replacement. The r9 approval does not cover this source deployment. After approval, the coordinator should stage the exact archive with owner-only mode, run preflight, execute deployment, observe the new service and Windows node, then perform the separately approved reopen. The old r9 authority helper remains pinned to its old source and must not be bypassed.

Live Store behavior and successful restart/reopen are unproven until that controlled deployment occurs. `packet-manifest.json`, `reopen-helper-manifest.json` and `store-lookup.diff` identify the concrete artifacts for review.
