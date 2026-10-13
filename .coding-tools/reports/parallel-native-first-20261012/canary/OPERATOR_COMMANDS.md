# Exact canary operator sequence

Source/package parity and the exact packaged controller/Recovery descriptor must
already be verified. These are local prepared helpers; none was invoked here.
Run the full Codex-web canary first, then the two-root overlap canary.

## 1. Codex-web build approval and full canary

Inside the already verified packaged controller, with its existing `enrollment`,
`targets` and descriptor-bound `exact` locals, call:

```javascript
const { installCanaryApprovals } = require('E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/canary/canary-policy-approvals.cjs');
const result = await installCanaryApprovals({
  enrollment, targets, expectedEpoch: '<exact current READY epoch>',
  observeActivation: () => exact('runtime.activation_epoch_status'),
  approvalSet: 'codex-build',
  fixtureManifestPath: 'E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/canary/fixture-preparation.json'
});
receiptFile('canary-policy-approvals', result);
```

This adds only `['node', 'trusted-build.js']` to the current Codex-web generation's
native prefixes, preserving its existing prefixes. It checks the exact prepared
script hash and READY epoch, installs `native_only` for this canary, and returns
the actual inspected policy digest. The root's controller must mark mutation
started before calling the helper and retain its usual partial-failure receipt.

After that install and the current heartbeat, capture a fresh sanitized server
readiness report with the root's current observer. Construct a new pins file:

```powershell
python -B .coding-tools/reports/parallel-native-first-20261012/canary/prepare-reviewed-canary-pins.py --kind codex-full --server-readiness 'ABS_FRESH_SERVER_REPORT' --approval-receipt 'ABS_CANARY_APPROVAL_RECEIPT' --fixture-manifest 'E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/canary/fixture-preparation.json' --output 'E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/canary/codex-ready-pins-NEW.json'
```

The builder requires server/approval observations within two minutes, current
node heartbeat/epoch, exact current binding/generation/pilot, actual policy and
serving source digests. It refuses stale or contradictory evidence and an
existing output path. It never creates authority or changes the database.

Run the existing wrapper with the generated pins and a new attempt:

```powershell
& .coding-tools/reports/parallel-native-first-20261012/canary/invoke-native-first-canary.ps1 -ExecuteConfirmedReadyPilot -ReadyPinsPath 'ABS_NEW_CODEX_PINS' -AttemptId 'NEW_GUID' -IncludeApprovedBuild
```

Require final original action settlement, task closure and writer release.
The 100 reads, 20 guarded patches/readbacks, 10 Node version Jobs, three Git
metadata Jobs and approved Node fixture build remain separately countable.
The successful build must match its expected artifact and FileAPI readback.

## 2. Two-root fixtures, approvals and overlap

Plan without writing:

```powershell
python -B .coding-tools/reports/parallel-native-first-20261012/canary/prepare-parallel-overlap-fixtures.py --codex-root 'E:/DEV/Codex-web' --autocad-root 'E:/DEV/Autocad'
```

Then use the same exact root arguments with `--prepare-fixtures --manifest-path`
set to an absolute new manifest in this canary directory. This creates only
the additive canary fixtures and no AutoCAD implementation/build edits.

Call the same controller helper with `approvalSet: 'overlap'` and that manifest.
It adds only `['node', 'tests/fixtures/parallel-native-overlap-20261012/hold.cjs']`
to each exact generation, retains the Codex build approval, verifies each script
hash/epoch and records actual per-root policy digests.

Capture a new fresh server report, then generate overlap pins:

```powershell
python -B .coding-tools/reports/parallel-native-first-20261012/canary/prepare-reviewed-canary-pins.py --kind overlap --server-readiness 'ABS_FRESH_SERVER_REPORT' --approval-receipt 'ABS_OVERLAP_APPROVAL_RECEIPT' --fixture-manifest 'ABS_TWO_ROOT_FIXTURE_MANIFEST' --quarantine-receipt 'E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/quarantine-receipt.json' --output 'E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/canary/overlap-ready-pins-NEW.json'
& .coding-tools/reports/parallel-native-first-20261012/canary/invoke-parallel-overlap-canary.ps1 -ExecuteConfirmedReadyTwoRootCanary -ReadyPinsPath 'ABS_NEW_OVERLAP_PINS' -FixtureManifestPath 'ABS_TWO_ROOT_FIXTURE_MANIFEST' -AttemptId 'NEW_GUID'
```

Require exact native receipts, positive same-node Job interval intersection,
original handles after HTTP observation-client reconnect, both new task/lease
closures, and unchanged historical UNKNOWN evidence. Source or fixture changes
require new reviewed pins/manifests; do not replay an uncertain original attempt.

## 3. Remaining focused proof

- **Local acceptance through runtime reconnect:** capture the exact patch RUN/
  WAVE IDs, ACCEPTING states and proof lineage from each local canonical ledger.
  During the root's controlled Windows refresh with `allowAcceptancePending`,
  preserve those facts, then observe identical IDs/states/proofs after restart.
  Generate new runtime pins before a new read/version probe. The canary's HTTP
  client reconnect does not prove this Windows restart boundary.
- **Semantic acceptance:** local `task_control accept` requires a passed proof
  on the exact mutation wave with current source binding. A patch/readback or
  a successful build from another RUN does not supply that proof. Audit the
  original RUN/WAVE first. If the original wave has no proof, reject it through
  the supported operator API, display its exact rejection checkpoint, then
  acknowledge the current persisted report ID and create a proof-only replan
  in the same scoped task/RUN. Adopt the existing postimage, execute the reviewed
  read-only fixture verifier, and accept only the new proven wave. Preserve
  original actions and the rejected wave; never replay patches or import proof
  from another RUN. The helper sequence is in `SEMANTIC_OPERATOR_COMMANDS.md`.
  The proof-only command uses ordinary local execution and does not establish
  native or zero-VM execution. Central task closure remains a separate fact.
- **Python compatibility:** one `['python', '--version']` Job with a small timeout
  and bounded output, using the existing safe native shape, can distinguish basic
  executable compatibility from the earlier Python token fixture failure. Keep
  original receipt/Job/error facts; no fallback/retry or inferred loader cause.
  This does not establish Python project or AutoCAD/.NET build compatibility.
- **Final product mode:** this helper pins `native_only` for strict canary proof.
  If the operated product must retain `native_first` fallback for other commands,
  the root should install that explicit final mode on the exact scopes after
  proof, preserve their reviewed native prefixes, then capture fresh observations.

## 4. Original read067 timeout reconciliation

Attempt `6bba02a734db47988da6042572f69497` verified 66 reads, then stopped on
original action `act_1de2cef3dc304d6e8b3f90237d7c136a` with one delivery attempt
and `CONTROL_PLANE_FILE_READ_TIMEOUT`. No patches or Jobs were dispatched.
The original UNKNOWN is evidence; a late successful bootstrap does not supply
the missing bounded read result.

Use the exact selected r3 packaged Electron controller
`parallel-r3-transition/packaged-operations.cjs` with mode `reconcile-read067`,
the existing `--parity-proof` and `--smoke-proof`, the exact current `--epoch`,
`--server-readiness ABS_FRESH_SERVER_REPORT`, and
`--local-evidence E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/local-read067-timeout-evidence.json`.
Without `--apply` or `--confirm-rejected-result` this performs a preflight.
For the reviewed append, add both flags. The controller rechecks the immutable
package, exact READY host and canonical absence of active work, creates a fresh
gate bound to the original central/local UNKNOWN evidence, and writes an
exclusive intent before requesting the rejected receipt.

The appended terminal result says `read_may_have_occurred=true`,
`valid_bounded_read_receipt_retained=false` and `read_success_claimed=false`.
It preserves the original UNKNOWN receipt and local journal. It does not replay
the action, invent successful content, or quarantine this current action.
If the append response is uncertain, observe the original action and intent;
do not repeat the mutation. Close the original task and writer through the
supported facade only after exact terminal settlement is verified. A new full
canary requires a new UUID and a fresh clean preflight boundary.
