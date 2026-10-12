# r13 exact one-dispatch canary — preparation only

Root owns live commands after explicit r13 activation, pilot rotation and one
MCP trial approval. This new subtree adapts the tested r12 helper and transport.
Old r12 files, markers, consumed intents and receipts remain untouched.

Exact fixture, patch, checker and 60-second plan remain unchanged. The new native
query-only preflight pins `source-fingerprint-1012-r13`, its 17 source payloads
and source-freeze hash `e9351a360eaa7c016514015a27ea06c762604e12c2a5ca436a550abbf09f29ff`.
It does not run the checker or start a service/Job.

The authority receipt must be the actual r13 reopened receipt:
`phase=r13_intake_observation`, `next_phase=intake_reopened`, exact newly approved
replacement pilot and revoked old pilot lineage, unchanged r12 context/requested
time/expiry, `approval_id=r13-same-window-transition`, and new marker digest.
The immutable r12 marker remains pinned to `a3c5c2ee…`. No new window is created.
Server evidence uses the distinct protected `r13-same-window-transition/canary-r13`
namespace and task/patch keys start `r13-initial-`. Incoming staging uses a fresh
`r11-approved-UTC` directory because the frozen transport validates that prefix;
it never reuses an earlier trial.

## Individual root commands

Use one exact Node/Python executable path already resolved by root. These are
individual existing helpers, with no additional shell orchestration wrapper.

1. Run `node ABSOLUTE_THIS_DIRECTORY/native-preflight.cjs` after ready r13 and
   exact scoped reopen. Save its exclusive public receipt.
2. Freeze a new pins file using `pins.template.json`. Copy authority scope and
   service identity from the actual reopened receipt, native fields from its
   `node` echo and fresh native receipt. Set exact hashes for authority/native
   receipt and new authority marker. Stable approval is
   `r13-same-window-transition`; native proof fields and old row hashes stay exact.
3. Within 60 seconds and with at least 12 minutes remaining:

```text
python -B C/root-canary-ssh.py prepare --pins ABSOLUTE_PINS
  --native-preflight ABSOLUTE_NATIVE --expected-native-preflight-sha256 ACTUAL_SHA
  --authority-receipt ABSOLUTE_R13_REOPEN --expected-authority-receipt-sha256 ACTUAL_SHA
python -B C/root-canary-ssh.py stage --manifest ABSOLUTE_RETURNED_MANIFEST --execute
python -B C/root-canary-ssh.py preflight --manifest ABSOLUTE_RETURNED_MANIFEST --execute
python -B C/root-canary-ssh.py dispatch --manifest ABSOLUTE_RETURNED_MANIFEST --execute
python -B C/root-canary-ssh.py observe --manifest ABSOLUTE_RETURNED_MANIFEST --execute
```

Dispatch exactly once. Repeat only read-only observe. Unknown dispatch/effect
requires read-only reconciliation; never delete a consumed intent or retry it.
After durable completion, the adapted `native-output-read.cjs` and
`correlate_r13.py` retain the r12 read-only Job/output/proof/source correlation
contract. Root must capture complete bounded TAP 4/4 and empty stderr within the
300-second output-retention period; exit zero alone is insufficient.

```text
python -B C/correlate_r13.py --receipt ABSOLUTE_OBSERVE
  --pins ABSOLUTE_PINS --output-receipt ABSOLUTE_NATIVE_OUTPUT
python -B C/root-canary-ssh.py cleanup --manifest ABSOLUTE_RETURNED_MANIFEST --execute
```

The Electron credential reader requires the exact existing profile and a root
launcher that clears `ELECTRON_RUN_AS_NODE`; it creates no BrowserWindow and
claims no ChatWeb attestation. Use the documented preserved r12 procedure with
the new r13 script path, not an array of executable paths.

## Proof and limits

Three focused offline tests cover correct rotated/reopened receipt, exact
window/scope/pilot/approval lineage denials and native identity/revocation drift.
Python AST and Node syntax checks pass; actual r13 package parity is checked by
the query-only package-proof function. Existing r12 core semantics and proofs
are reused; only new authority/namespace/package bindings were changed.

No live SSH/API/IPC, canary dispatch, activation, native semantic acceptance,
deploy, service restart, reboot, commit or push occurred in this lane. Git remains
dirty `main @ 2c554f59…`. Genuine native semantic acceptance remains a separate
controller operation; these helpers never fabricate it or settle old RUN/WAVE.
