# Native-first local transition preparation

Prepared on 12 October 2026 for the exact existing Windows r9e production
installation. This document records a guarded next sequence; no production
transition or workspace/policy change was performed by these observations.

## Current verified installation

- Recovery Host PID: `38436`
- Start token: `134362736855547600`
- Instance: `b81bbad41b65c71f1bb4f21b0bdb8d10`
- Installation: `2e511714fe3f1f64484f11778e1fe2a5c46bb5d5873f02047144b417f7996d0a`
- Epoch: `activation-mv53i8gp-f06eeb5b46a11d2cf7ebdc9445606937`, READY/OPEN
- Native default workspace: `E:\DEV\Codex-web`
- Authorized additional root: `E:\DEV\Autocad`
- Exact local census: zero live commands, managed jobs, background operations,
  agent lanes and owned live runs; only expected serving-runtime PID blocker.
- Existing AutoCAD registration and local policy bytes were preserved.
- Production UI is currently missing and recovery is suppressed by the
  existing `operator_quit` receipt. Missing UI is separate from MCP readiness.

The source for these claims is
`production-transition-preflight-1791803582244.json`. It is a point-in-time
observation and must be refreshed before any lifecycle operation.

## Gate currently open

Three AutoCAD actions have durable submitted UNKNOWN bounded-file-read
receipts. `local-unknown-file-read-action-evidence.json` retains the exact
action/attempt correlations. The server independently reports matching
UNKNOWN receipts and no open tasks, writer leases, queued or dispatched work.

`file-read-source-effect-phase-correction.json` proves that generic
`CONTROL_PLANE_FILE_READ_TARGET_MISSING` can be raised both before Recovery
dispatch and during post-read absolute-path validation in installed r9e.
Therefore these historical actions cannot be reclassified as rejected merely
from that code. Original UNKNOWN rows/receipts remain preserved. No retry,
completion, quarantine, rejected receipt or SQL mutation was performed.

The future source fix separates the pre-dispatch diagnostic as
`CONTROL_PLANE_FILE_READ_TARGET_MISSING_BEFORE_DISPATCH`; it does not change the
meaning of the historical generic diagnostic.

## Candidate proof before changing production

1. Finish source edits and build a fresh immutable candidate.
2. Require exact source/package parity and isolated packaged smoke for that
   candidate, including terminal fixture processes and unchanged production
   descriptor. r2 and r4 have smoke proof but are stale for subsequent source
   edits and are not final activation candidates.
3. Refresh authenticated server census and exact local preflight. Zero live
   work is necessary; the remaining UNKNOWN reconciliation/workspace gate must
   also be satisfied through supported evidence-preserving APIs.

## Exact local installation handoff

The historical `r9e-transition` helpers pin an older r9d owner PID `3476` and
must not be replayed against current r9e. Prepare a new additive helper pinned
to the current descriptor, current old-package hashes and final new-package
proof. Keep mutation disabled until all gates are satisfied.

The supported sequence is:

1. Confirm server idle evidence is fresh (at most 120 seconds), local canonical
   census and exact old owner are unchanged, and UNKNOWN action handling is
   officially admitted.
2. Perform one supported ordinary stop and immediately retain its producer
   receipt. On uncertain response, observe/reconcile that exact operation;
   do not replay it or substitute a process-name kill.
3. Verify Coding MCP/native executor terminal, stopped canonical census, exact
   owned UI suppression/exit, Recovery Host identity and no live owned
   Sandbox executor before exact host retirement.
4. Install the final candidate's supported Recovery Supervisor for the same
   data root only after an exact fresh retirement receipt. Launch its UI/Host
   and perform supported full-clean refresh with preserved historical
   acceptance. A refresh before installation handoff would reload r9e.
5. Verify a new epoch/process identities, loaded source receipts, connector
   freshness mode, central authority and final census before READY/OPEN.
6. Change shortcuts only after a fresh exact READY/OPEN receipt and preserved
   original shortcut fingerprints.

No durable ledger, registry, policy, task history or unknown action is deleted.

## Codex-web native-first canary and AutoCAD restoration

Existing packaged enrollment APIs are the intended path:

```javascript
await enrollment.listWorkspaces();
await enrollment.activateWorkspace({ workspaceId, workspaceGeneration, confirmActivate: true });
await enrollment.installStandingWorkspaceFilePolicies({ workspaceId, workspaceGeneration,
  allowWrite: true, replaceExisting: true });
await enrollment.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration,
  executionMode: 'native_first', nativeArgvPrefixes: [], probeSandbox: false,
  replaceExisting: true });
```

Use the already registered exact Codex-web ID/generation from fresh inventory;
do not register or replace it. Native default already points to Codex-web, so
no new root grant is required. Activation must pass current-device live-work
and unresolved current-scope action checks. The shared service principal
currently delegates only AutoCAD; local registry presence is not Codex-web
dispatch authority. Coordinate the supported scoped-pilot selection with the
Control Plane lane, then observe fresh exact delegation/contract before
policy installation or any canary.

Local standing read/edit/exec policy files are singletons. Installing Codex-web
policies temporarily replaces the active local AutoCAD policy. Preserve the
original policy hashes and complete this deliberate scope sequence, including
restoration; do not copy raw policy JSON or transfer native approvals between
workspace IDs/generations.

For a canary, create a fresh exact task/writer intent and run a bounded safe
metadata command such as `git status --short --branch`. Require the actual
receipt/Job to report `execution_backend=native`,
`isolation_level=process_container`, expected policy decision, exact
command/job/run identity, terminal status and no VM adapter invocation. File
read/edit checks use File API receipts and need no VM. Failed actions remain
their own durable evidence; do not reuse their IDs for a new trial.

After the canary, close/release only its exact task/writer through supported
APIs, refresh both server and local census, restore the exact AutoCAD
registration/pilot selection through supported activation and reinstall its
standing policies with native-first mode and its own approved prefixes.
Observe exact AutoCAD binding/generation/contract, policy receipts, zero live
canary work, preserved unknown history and final READY/OPEN status.

If the historical UNKNOWN gate cannot be satisfied safely, finish with the
validated source/package and explicit pending activation instead of changing
production or claiming the canary succeeded.
