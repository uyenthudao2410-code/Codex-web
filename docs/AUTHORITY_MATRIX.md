# Authority Matrix

This matrix is the bounded inventory of identity fields that participate in
Coding Web execution, recovery, evidence, or continuity. It is intentionally a
decision aid, not a second state machine. The implementation and focused tests
remain authoritative; this document records where each identity is allowed to
grant authority and where it is only an observation or a reference.

**Source snapshot:** repository `main`, HEAD `148de18795787e820ef1bc51d0f2591052d24238`.
The worktree is dirty, so this snapshot is a source reference only. It does not
claim that the currently loaded Electron/MCP process has this revision.

## Decision rules

1. An identity grants authority only at the gate named in the matrix and only
   when the gate verifies the complete, exact tuple it requires.
2. A value read from a projection, process table, port, timestamp, or old
   report is an observation until the owning authority verifies it.
3. IDs are never reconstructed from proximity, ordering, current UI state,
   `last_active_workspace`, or a global “current run” fallback.
4. Restart-safe identities may be persisted, but persistence alone never proves
   that the current process still owns the identity.
5. Hashes identify bytes or a contract; they do not grant permission to mutate
   those bytes or to claim a user outcome.

## Matrix

| Identity | Fact identified | Can grant authority? | Created / invalidated by | Survives restart? | May be inferred? | Canonical enforcement / evidence |
|---|---|---|---|---|---|---|
| `workspace_id` | Stable logical identity of one registered workspace root | Yes, for workspace scoping only, when paired with the exact root and generation | Workspace registry / scope resolver; invalidated when the registered root identity changes | Yes | No | `workspace_scope.py`, `workspace_context`; explicit workspace binding tests |
| `workspace_generation` | Current generation of a registered workspace binding | Yes, as a stale-write fence when the expected generation matches | Workspace registry mutation; invalidated on switch or guarded replacement | Yes | No | Workspace registry and generation checks in the MCP server/runtime |
| `task_context_id` | One stateless request/context binding used to select task-local projections | No, by itself | Caller/context bridge; invalidated when the context is absent, malformed, or points at another workspace | No; a new request must supply it | No | Public input schema injection and task/workspace binding in `server.py` |
| `task_id` | Durable workflow/task parent | Yes, only for operations explicitly bound to that task | Canonical task ledger; terminal task state closes the parent | Yes | No | Orchestration ledger and `task_control` exact-target validation |
| `run_id` | One canonical execution run and its event chain | Yes, for run-scoped mutation when the exact run is supplied and owned | Ledger run creation; terminal transition, reconcile, or abort invalidates further mutation | Yes | No | `OrchestrationLedger`, run-bound `task_control`, event-chain checks |
| `wave_id` | One attempt/wave under an exact run | Yes, only with its exact parent `run_id` | Ledger wave creation; terminal wave/checkpoint closes the attempt | Yes | No | Run/wave foreign-key and parent-state checks |
| `controller_lease_id` / `write_lease_id` | Exclusive controller or workspace-write lease | Yes, for the lease-fenced mutation it covers | Lease acquisition; expiry, release, fencing, or owner replacement invalidates it | Yes, as durable history; live authority does not survive owner loss | No | Lease/write-fence paths in `coordination.py` and ledger tables |
| `operation_id` | Idempotency identity for one exact command/request | No; it permits exact retry only | Caller/request kernel; conflicting request hash invalidates reuse | Yes, in execution records | No | Execution kernel operation/request hash conflict checks |
| `managed_process_job_id` | One governor-owned process/job record | Yes, for lifecycle cleanup only after exact PID, process token, owner, and workspace checks | Execution resource governor; process exit/reconcile terminalizes it | Yes, as evidence | No | `execution_resources.py`, managed-process census and reconciliation script |
| `activation_epoch_id` | One controlled runtime activation transaction | Yes, for activation admission and completion within the exact epoch | Recovery Host/activation coordinator; completion, failure, or close invalidates it | Yes | No | `activationEpoch.js`, activation capability and full-clean coordinator |
| `activation_operation_id` | One activation request/fence within an epoch | Yes, only for the matching activation operation | Activation coordinator; expiry, cancel, or terminal epoch invalidates it | Yes | No | `activation_capability.py`, Recovery Host IPC allowlist |
| `process_instance_id` | Current Coding MCP process instance | Yes, to reject stale/replaced process claims | MCP process start; process exit/replacement invalidates it | No | No | Runtime snapshots, process identity/token probes, activation postflight |
| `server_instance_id` | Current MCP HTTP/server instance behind a process | Yes, for current connector/runtime contact evidence | MCP server start/replacement | No | No | Runtime snapshot and connector contact receipts |
| `device_instance_id` | Current live runner/device process instance | Yes, to fence stale endpoint claims | Device/runner start; replacement or liveness loss invalidates it | No | No | Device identity and recovery-plane status |
| `installation_id` | Exact installed application/runtime identity | Yes, to reject a foreign installation | Installation/runtime identity derivation; package/install replacement changes it | Yes for that installation | No | `runtimeIdentity`, Recovery Host descriptor installation match |
| `checkpoint_id` | Accepted source checkpoint record | Yes, as the source admission handle for controlled activation | Acceptance/checkpoint transition; superseded or invalid proof closes it | Yes | No | Five-field `source_checkpoint` validation in `acceptance_receipts.py` and `activationClosure.js` |
| `git_head` | Exact repository commit named by a checkpoint | No, evidence only; it becomes an activation precondition inside the checkpoint tuple | Git commit; mismatch invalidates the checkpoint binding | Yes | No | Activation source checkpoint and worktree/source checks |
| `proof_fingerprint` | Content identity of the accepted proof bundle | No, evidence only; never a user-outcome claim | Proof bundle generation; changed proof bytes invalidate it | Yes | No | `passed_proof_fingerprint`, accepted receipt reconciliation |
| `worktree_fp` | Exact guarded source/worktree state observation | No, evidence only | Worktree changes; mismatch invalidates guarded continuation | No | No | Worktree fingerprint and guarded edit/acceptance paths |
| `problem_id` | One user problem lineage | No by itself; it scopes problem evidence | Problem-lineage runtime; explicit open/reopen/revise | Yes | No | `problem_lineage.py` |
| `problem_revision` | One immutable revision of a problem contract/frame | Yes for revision-scoped claims only when exact revision and contract fingerprint match | Explicit revise CAS; superseded revision becomes historical | Yes | No | Problem revision CAS and resolution-envelope checks |
| `contract_fingerprint` | Canonical bytes of the problem/resolution contract | No; it detects drift and binds evidence | Canonicalization of the supplied contract; any semantic change changes it | Yes | No | Problem-lineage and resolution-envelope reconciliation |
| `capsule_id` | One bounded handoff/continuity capsule | No; it can restore context but cannot grant mutation authority | Handoff writer; superseded/stale capsule is rejected or refreshed | Yes | No | Handoff capsule privacy, size, hash, and freshness checks |
| `p5_assignment_id` | Immutable treatment/control assignment for a P5 epoch | Yes only inside the pre-write assignment fence | P5 assignment protocol; epoch close/hard-stop invalidates live use | Yes | No | P5 assignment and pre-write binding checks |
| `connector_contract_sha256` | Exact public tool-contract bytes | No; discovery/compatibility evidence only | Current server contract generation; changed schema requires discovery/compatibility gate | Yes as a receipt | No | `runtimeOrchestrator.connectorContractStatus`, discovery receipts |
| `connector_rediscovered_at` + process/server IDs | Fresh current-process connector contact | Yes only to satisfy connector freshness/ACK gate | Fresh `tools/list` or `server/discover`; stale contact invalidated by process/server replacement | No | No | Recovery Host connector acknowledgement gate |

## Required tuples at important gates

| Gate | Exact tuple / predicate | What it proves | What it does **not** prove |
|---|---|---|---|
| Read-only task observation | `task_context_id` + explicit workspace binding | The request is scoped to the selected task/workspace projection | Ownership of a run, lease, or process |
| Run-bound mutation | `task_id` + `run_id` + `wave_id` + active owner/lease | The mutation targets the intended canonical execution | That the process is current or that the user problem is solved |
| Controlled source activation | `checkpoint_id`, `run_id`, `wave_id`, `proof_fingerprint`, `git_head` plus activation operation/epoch | The exact accepted source packet is eligible for activation | Current connector discovery, production release, or natural outcome |
| Runtime freshness | `installation_id` + `device_instance_id` + `process_instance_id` + exact running/disk revision | The observed process is the intended current installation/process | User acceptance or production health |
| Connector acknowledgement | Current contract SHA + fresh current-process discovery/contact + matching server/process IDs | The connector has contacted this runtime contract | That any tool call is authorized for a different workspace |
| Context continuation | Fresh capsule hash/revision + workspace/source freshness | Compact continuity without transcript replay | Any permission, lease, acceptance, or release authority |

## Open gates at this source snapshot

The matrix itself is source/documentation work. The following runtime gates
remain intentionally open until their owning authority produces fresh evidence:

- lifecycle census has no unexplained active run or unbound live resource;
- loaded runtime revision equals the intended disk revision;
- Coding MCP/Tunnel are live and fully ready;
- a fresh current-process `tools/list` or `server/discover` receipt exists;
- one immutable accepted baseline includes lifecycle, runtime, contract, and UI
  performance evidence;
- a natural user problem has an independent outcome receipt.

No row in this document authorizes restart, process adoption, ledger repair,
release, push, deployment, or production promotion.

