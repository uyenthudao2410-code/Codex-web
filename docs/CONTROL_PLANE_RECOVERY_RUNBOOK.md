# Control Plane Recovery and Restore Runbook

**Status:** operator procedure and acceptance contract. It is not evidence that
backup, retention, restore, reconciliation, or a drill has happened on Ubuntu.

This runbook applies only to the Python `control-plane` SQLite database used by
the Ubuntu control-plane pilot. It does not authorize changes to the Windows
Electron runtime, Coding MCP, tunnel, local workspace, `.coding-tools` ledger,
or a remote node. It complements the current implementation status and plan:

- [Control-plane implementation status](CONTROL_PLANE_IMPLEMENTATION_STATUS.md)
- [Ubuntu 24/7 completion plan](UBUNTU_24X7_COMPLETION_PLAN.md)
- [Control-plane API and snapshot contract](../control-plane/README.md)

## 1. Non-negotiable recovery invariants

1. A central SQLite snapshot is not a record of effects that may already have
   occurred on a Windows node. Restoring central state must never re-send a
   possible effect merely because the restored database says it is queued.
2. Place central admission in durable `recovery` before any authorized restore
   or recovery drill. `recovery` rejects new intent/action admission and poll
   delivery while continuing to accept authenticated late receipts for
   reconciliation.
3. Do not copy a live SQLite database with filesystem copy commands, merge
   databases, edit its rows directly, delete WAL/SHM sidecars to silence an
   error, or replace the production database in place as the first exercise.
   Use the verified snapshot command and inspect the completed artifact.
4. A restore drill first uses an isolated service/database location. It must
   not share the production database path, credentials, listener, node policy,
   or central actor authority.
5. No action in `dispatch_unconfirmed`, `accepted`, or `reconcile_required`
   becomes safe to retry until an operator has node-side evidence for its exact
   action/attempt/context/generation scope. Missing evidence remains
   `outcome_unknown`; it is not rewritten as cancelled, completed, or absent.
6. Reopening admission is an explicit owner decision after reconciliation. A
   healthy service, a successful SQLite integrity check, or an empty queue is
   not authorization to reopen.
7. Never put operator tokens, node credentials, headers, SQLite content,
   workspace paths, source code, prompts, or raw receipts into this runbook,
   Git, chat logs, or a completion report.

## 2. Required authority and preflight packet

Before starting a drill or restore, an operator must record the following in a
separate, access-controlled incident/change record. Do not proceed when any
entry is unknown.

| Required item | Evidence required | Why it matters |
| --- | --- | --- |
| Named owner and change authority | Person/team authorized to alter the named Ubuntu service and storage target | Prevents an accidental change to a different service or shared host |
| Exact target | Ubuntu host, service unit, protected environment reference, database path and isolated-drill path | A branch name, friendly host label, or remembered path is insufficient |
| Source/package identity | Selected deployment receipt, declared revision, `package_source_sha256`, expected fingerprint, `service_instance_id` | Distinguishes source package proof from the running service/unit identity |
| Current health and admission | Fresh `/healthz` record and authenticated admission observation captured without secrets | Establishes the before-state; health alone is not write-admission proof |
| Inventory | Owner-scoped node/context/request/action observations, including outstanding delivery states | Identifies work requiring node-side reconciliation |
| Node scope | Exact device, endpoint, workspace generation, local policy and connector state for every affected node | A central record cannot substitute for local authority/effect evidence |
| Retention/ACL plan | Backup directory owner/mode, encryption arrangement, retention rule, free-space alert threshold and deletion owner | Snapshot tooling deliberately does not configure these operational controls |
| Approval boundary | Whether this is isolated drill, production restore, reconciliation only, or admission reopen | These are separate operations and require separate authority |

Stop and create a checkpoint if the target, owner, source package, service
identity, database location, node scope, or recovery authority cannot be
verified. Do not compensate by stopping an arbitrary service, changing
environment variables, restarting a component, or fabricating a receipt.

## 3. Safe preparation commands and read-only deployment comparison

These commands are local, explicit preparation primitives. They do not start a
server, alter central admission, contact a node, or perform a restore. The
candidate command creates a separate artifact marked `recovery`; it does not
change the admission state of any running service.

```powershell
# Run from the exact selected package/check-out.
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.maintenance package-fingerprint

# Run only on the host that owns the selected existing SQLite source.
python -m control_plane.maintenance snapshot `
  --source '<existing-control-plane.sqlite3>' `
  --destination '<new-nonexistent-snapshot.sqlite3>'

# Inspect a completed snapshot before restore planning.
python -m control_plane.maintenance inspect-snapshot `
  --source '<completed-snapshot.sqlite3>' `
  --expected-sha256 '<snapshot_sha256-from-snapshot-receipt>'

# Only after the relevant drill/restore authority has been recorded, prepare a
# new recovery-locked artifact. It never replaces the central database.
python -m control_plane.maintenance prepare-recovery-restore `
  --source '<completed-snapshot.sqlite3>' `
  --destination '<new-recovery-candidate.sqlite3>' `
  --expected-sha256 '<snapshot_sha256-from-snapshot-receipt>'
```

Capture only the content-free receipts: operation name, snapshot/package hash,
integrity result, schema version, admission mode, delivery-state counts and
unresolved-action count. The snapshot command refuses a missing source or an
existing destination. Inspection uses SQLite `mode=ro&immutable=1` and refuses
WAL/SHM sidecars, malformed/mismatched digest, and integrity failure. The
candidate command additionally requires the current schema and a valid source
admission value, refuses an existing destination, persists `recovery` only in
the new candidate, and returns source/candidate hashes without paths.

The maintenance commands do not establish storage ACLs, retention, free-space
monitoring, package deployment, systemd ownership, source checkout identity,
node effect outcome, or restore safety.

After an authorized deployment has selected an exact package and set its
protected expected fingerprint, an operator may perform this additional
credential-free **GET-only** comparison before accepting package identity in
the preflight packet:

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.deployment_verifier `
  --health-url 'https://<private-control-plane>/healthz' `
  --expected-package-source-sha256 '<sha256-from-selected-package-receipt>' `
  --expected-admission recovery
```

Use `open` only when that is the separately observed durable before-state; use
`recovery` once the authorized operator has changed and read back the intended
recovery state. The verifier requires `service`, `ok`, SQLite integrity, the
current schema, expected admission, a valid `service_instance_id`, and both
actual and protected expected package fingerprints to match. It returns a
content-free receipt or a typed failure such as
`CONTROL_PLANE_DEPLOYMENT_HEALTH_INCOMPLETE`; it does not echo endpoint/body
content. It does **not** authenticate the operator readback, inspect systemd,
prove service owner/path/configuration/checkout/TLS, or authorize any restore,
admission change, process operation, node call, or canary. A failed/missing
health field leaves package identity unknown and stops the affected procedure.

## 4. Normal backup operation

The cadence, retention interval/count, encryption/key-management mechanism,
backup directory and free-space threshold are currently **unsettled operational
decisions**. Do not invent values in this runbook. The owner must choose and
record them before calling the operation production-ready.

For each authorized snapshot, preserve a minimal, non-secret receipt with:

1. UTC capture time and named service/database target reference.
2. Selected package fingerprint/revision and current service instance ID.
3. Snapshot artifact SHA-256, integrity result, schema version and byte count.
4. Storage policy identifier, encryption/ACL check result and available-space
   observation.
5. Retention decision, deletion owner and any exception/failure.

The canonical live database and evidence under `.coding-tools/**` are not
backup scratch space. Do not store service snapshots in the repository or
delete `.coding-tools` data under a retention policy for this control plane.

## 5. Isolated restore drill sequence

An isolated drill verifies the procedure without changing production central
state or a node. It does not count as a production restore or canary.

1. **Authorize and freeze scope.** Record the exact isolated target, source
   package, selected snapshot receipt, owner, time window and abort owner.
   Confirm the isolated target has no production listener, DB path, node secret,
   local bridge policy or authority to dispatch to a node.
2. **Capture before-state.** Record fresh production health/admission and
   owner-scoped outstanding-action inventory without secrets. Do not infer that
   zero currently visible actions proves no historical effect.
3. **Enter recovery on the intended central target.** The authorized operator
   changes durable admission to `recovery` using the authenticated operator
   surface, then reads it back. If this cannot be proven, do not continue to a
   production restore; retain the incident as blocked.
4. **Create and inspect the source snapshot.** Use the verified snapshot and
   immutable inspection commands above. Abort if either receipt is not `ok`,
   hashes differ, sidecars exist, schema is unexpected, or artifact storage
   fails the approved ACL/space policy.
5. **Prepare the recovery-locked candidate.** Use
   `prepare-recovery-restore` with the inspected snapshot's exact SHA-256 and
   a new isolated destination. Verify its candidate hash, schema and durable
   `recovery` admission in the content-free receipt. This does not itself
   restore or switch a service, and it must not target the production DB path.
6. **Restore only into the isolated location.** Use the reviewed candidate and
   an owner-approved recovery method appropriate to the named host and service.
   Do not include generic copy/replace commands here: the exact target, service
   manager, encrypted storage and rollback point must be reviewed in the change
   record first.
7. **Start only the isolated service according to its approved unit/config.**
   Verify that it has a distinct listener, database path, service instance, and
   no node dispatch capability. A successful process start is not recovery
   acceptance.
8. **Inspect restored state.** Capture health, schema/admission, package
   fingerprint and action delivery-state counts. Compare them to the snapshot
   receipt. Any divergence is `INCONCLUSIVE` until explained; do not rewrite
   the snapshot or adjust the expected result.
9. **Exercise reconciliation without effects.** Use fixture/observation paths
   that cannot call a Windows node to confirm that queued, dispatched,
   accepted, and unresolved records are distinguishable. Do not make a bridge
   call, create a binding, or force a receipt merely to obtain a green drill.
10. **Terminate isolated scope.** Stop only the named isolated service by its
   approved procedure and preserve its minimal receipts. Do not delete the
   production source database, snapshot, evidence, or unrelated worktree data.
11. **Checkpoint.** Record PASS, FAIL, or INCONCLUSIVE; measured duration;
    restoration point; unresolved-state counts; manual interventions; and all
    remaining external gates.

## 6. Production restore and reconciliation sequence

Production restore is a separate, explicitly authorized incident operation.
The isolated drill above is a prerequisite evidence source, not permission to
restore production.

1. Revalidate the Section 2 packet against the live target immediately before
   action. Record the current source/package fingerprint and service instance.
2. Keep central admission in `recovery`. Confirm the write/readback receipt;
   late authenticated receipts may be accepted, while new work and poll delivery
   remain blocked.
3. Preserve fresh before-state: verified backup receipt, immutable inspection,
   action/attempt/receipt inventory, node/context/binding state and affected
   local handles where the node is reachable.
4. Restore only with the approved exact service/database procedure. If the
   process, path, checkpoint, storage encryption, source package, service
   account or expected fingerprint differs from the approved packet, abort.
5. After restore, observe the central database in recovery mode. Classify every
   nonterminal action as `queued`, `dispatch_unconfirmed`, `accepted`,
   `reconcile_required`, or an explicit terminal receipt. Do not redeliver
   potentially sent work merely because a restored action is queued.
6. Reconcile at each reachable node using exact device/endpoint/workspace
   generation/action/attempt identity and its current local authority. A node
   that is offline, stale, changed, revoked, expired, or lacks trustworthy
   effect evidence leaves the action unresolved.
7. For effects that may have happened, obtain truthful node-side observation or
   an authorized operator decision with durable rationale. Never manufacture a
   completed/cancelled receipt. Preserve late receipts as evidence and reject
   stale authority from creating a new effect.
8. Reopen central admission only when the authorized owner accepts the complete
   reconciliation packet, proves the relevant old authority is fenced/quiescent
   where mutation is in scope, and confirms no pending action can be redelivered
   incorrectly. The owner records the exact reopen decision; health alone is
   insufficient.
9. If any action remains unknown, retain `recovery` or a narrower explicit
   maintenance boundary. Report the unresolved scope and next human action;
   do not claim restoration is complete.

## 7. Required evidence and acceptance

### T13 — restore of an older central database

PASS requires all of the following, not just `integrity_check=ok`:

- a verified, immutable-inspected snapshot receipt bound by SHA-256;
- durable admission closed to new delivery before restore;
- isolated-drill result for the exact procedure/version, then a separately
  authorized production operation if one is needed;
- action/attempt/receipt state comparison before and after restore;
- reconciliation proof for every may-have-sent scope, or a truthful unresolved
  state that prevents reopen/redelivery;
- owner-recorded reopen/retain-recovery decision with exact target identity.

### T14 — full disk or SQLite commit failure

PASS requires a deliberately authorized isolated fault test showing that the
system does not claim durable intake or send a new action when the transaction
cannot commit. It must record fault method, package/service identity, expected
and observed error, action/receipt state, cleanup result and recovery decision.
No test may fill a production disk or use an arbitrary shared filesystem.

### Drill report schema

Use a separate protected report with only:

| Field | Required value |
| --- | --- |
| Scope | `isolated_drill`, `production_restore`, or `reconciliation_only` |
| Identity | Host/service/database reference, package fingerprint, declared revision, service instance |
| Snapshot | Receipt hash, integrity/schema/admission, storage-policy result |
| Before/after | Delivery-state counts and unresolved count, without payloads/paths/secrets |
| Node reconciliation | Device/endpoint/context/action/attempt IDs or redacted references; observed/fail/unknown |
| Decision | `retain_recovery`, `reopen_authorized`, `abort`, or `inconclusive` with owner and rationale |
| Measurements | Start/end UTC, elapsed time, data-loss window observed, manual interventions, failures |

Do not report an RPO, RTO, HA level, uptime, recovery success, or business
outcome without an actual recorded drill or incident result.

## 8. Abort, rollback and escalation

Immediately stop phase expansion and keep/return the relevant central target to
`recovery` when any of these occur:

- package fingerprint, expected fingerprint, schema, unit, path, service
  instance or target identity differs from the approved packet;
- snapshot inspection fails, shows sidecars, or its digest differs;
- secret/credential exposure is suspected;
- a node may have executed an effect but cannot supply trustworthy evidence;
- a node workspace/generation/actor is stale or wrong;
- storage ACL, encryption, capacity or retention evidence is missing;
- a restore would require replacing a live database by an unreviewed command;
- an operator asks to bypass policy, strict runtime, connector, binding, receipt
  or reconciliation checks to obtain a green status.

At abort, preserve facts and receipts, report the unresolved scope, and request
the exact owner action. Do not reset the worktree, delete snapshot evidence,
remove database sidecars blindly, kill unrelated processes, create a second
writer, or send an execution retry.
