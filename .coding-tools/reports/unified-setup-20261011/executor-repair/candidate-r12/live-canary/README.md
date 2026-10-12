# New r12 canary packet — preparation only

Root owns every live operation. This subtree adapts the frozen r11
`live-canary-contract-sync` trial; old helpers, intents, authority markers and
receipts remain unchanged. No new public product schema is introduced.

## Exact behavior and scope

- Current candidate `policy-contract-1012-r12`, archive
  `2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1`;
  source freeze `dcdeaf4a8c49b5451dea2a239e4f512854edb3ba9b0117d021c5cbc15d2d6069`.
  The new native preflight rechecks all 15 frozen payloads, their current source,
  executable and Python hashes; it does not use an r11 parity guard.
- New server owner directory
  `/home/svhome/.local/state/codex-control-plane/owner-operations/r12-initial-verification-60m`,
  authority marker `authority-renewal-public.json`, and separate `canary` child.
  The r12 authority helper creates the empty protected child during close/reopen.
- The new 60-minute window, approval, context/pilot/service and marker digest
  come from the actual `r12_intake_reopened` public effect receipt. Root pins its
  exact file SHA256; local preparation and the remote canary compare it with
  the protected live marker. No future date/context/pilot is invented.
- Prior r11 next-marker remains pinned SHA256
  `e3d29f73b0395dd47ff46dd9bbb62831afce0a14183d23c2cd0ca88c5ceaf34c`.
  The unchanged common guard remains SHA256
  `c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f`.
- Same exact fixture patch and checker; verification is
  `argv=["node","--test","tests/fixtures/initial-proof-canary-check.cjs"]`,
  `cwd=""`, timeout `60000`, output bound `32768`. The Sandbox gate stays intact.
- Local prepare, server preflight and immediately-before-patch dispatch require
  at least `720000ms` remaining: the action's unclamped `600000ms` internal
  context plus `120000ms` margin. Server phases use the actual overview clock.
- A separate immutable dispatch intent precedes the first task effect; new
  keys use `r12-initial-task-` and `r12-initial-patch-` bound to exact pins.
  Unknown effects are observed/reconciled, never automatically replayed.
- Genuine authenticated Recovery IPC preflight requires final READY/admission,
  exact current native identities and native contract
  `0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4`.
  The principal-specific facade contract is separately fetched from tools/list
  and inventory immediately before dispatch. Neither digest substitutes for
  the other.

## Root sequence after approval, transition and exact scoped reopen

Use absolute paths. Let `C` be this directory. Do not invoke these live commands
until root has the new r12 activation and exact-scope authority authorization.

1. Run `node C/native-preflight.cjs`. It performs query-only authenticated IPC,
   exact source/package checks and read-only canonical census; only a new public
   receipt is saved. This does not run the checker or start a process/service.
2. Create one immutable pins file using `pins.template.json` shape. Copy window,
   context/pilot/service/approval from the actual reopened receipt; copy native
   identities and `native_preflight` fields from the native receipt. Add exact
   authority receipt/native receipt hashes and `next_marker_sha256`. Keep the
   historical row hashes intact; zero/template values are intentionally rejected.
3. Within the native receipt's 60-second freshness gate:

```text
python -B C/root-canary-ssh.py prepare
  --pins ABSOLUTE_NEW_PINS_JSON
  --native-preflight ABSOLUTE_NATIVE_RECEIPT_JSON
  --expected-native-preflight-sha256 ACTUAL_NATIVE_FILE_SHA256
  --authority-receipt ABSOLUTE_R12_REOPEN_RECEIPT_JSON
  --expected-authority-receipt-sha256 ACTUAL_AUTHORITY_FILE_SHA256
```

4. Use the returned immutable `staging-manifest.json` for:

```text
python -B C/root-canary-ssh.py stage --manifest ABSOLUTE_MANIFEST --execute
python -B C/root-canary-ssh.py preflight --manifest ABSOLUTE_MANIFEST --execute
python -B C/root-canary-ssh.py dispatch --manifest ABSOLUTE_MANIFEST --execute
python -B C/root-canary-ssh.py observe --manifest ABSOLUTE_MANIFEST --execute
```

Dispatch exactly once. Repeat only read-only observe. The transport reuses the
frozen binary-safe STAGE/INVOKE from r11 by exact hash; its incoming-directory
prefix therefore stays `r11-approved-<fresh UTC>`. This is a new directory
containing r12 helpers/receipts, not reuse of an old trial. Its six files are
common, r12 canary, exact patch, pins, native receipt and authority receipt.

5. After durable completion, immediately capture retained TAP output using the
   adapted `native-output-read.cjs` through an isolated Electron credential
   reader in the authorized profile. It requires an explicit
   `--user-data-dir=C:\Users\daoth\AppData\Roaming\web-mcp-assistant`, creates
   no BrowserWindow/production mutex, sends truthful client type `electron`,
   and claims no ChatWeb attestation:

```text
ELECTRON_UNDER_ROOT_CONTROL --user-data-dir=AUTHORIZED_PROFILE C/native-output-read.cjs
  --observation=ABSOLUTE_OBSERVE_RECEIPT --observation-sha256=ACTUAL_SHA256
  --pins=ABSOLUTE_NEW_PINS_JSON --pins-sha256=ACTUAL_SHA256
  --completed-at-ms=ACTUAL_DURABLE_JOB_COMPLETION_MS
  --receipt=C/native-output-UTCSTAMP.json
```

The actual launcher must clear `ELECTRON_RUN_AS_NODE` and use the authorized
crypto profile as in the preserved r11 output-reader procedure. Capture complete
bounded stdout/stderr before 300 seconds of output retention expire. It proves
actual TAP 4 pass/0 fail and empty stderr; it never infers 4/4 from exit 0.

6. Correlate the exact Job/proof/RUN/WAVE/source/runtime and submitted node
   receipt against the real ledger in `mode=ro/query_only`:

```text
python -B C/correlate_r12.py --receipt ABSOLUTE_OBSERVE_RECEIPT
  --pins ABSOLUTE_NEW_PINS_JSON --output-receipt ABSOLUTE_OUTPUT_RECEIPT
```

7. Cleanup only the settled exact new central task/writer:

```text
python -B C/root-canary-ssh.py cleanup --manifest ABSOLUTE_MANIFEST --execute
```

Keep new native semantic acceptance pending and historical RUN/WAVE row hashes
unchanged. A central MCP service trial is not native ChatWeb final acceptance.
No helper accepts a RUN, fabricates attestation or changes a Console verdict.
Root still needs a final quiescent Job/VM census and an operator checkpoint.

## Offline proof and limits

- 19 tests: own-context causal proof, unchanged database/history, unrelated
  context rejection, immutable intent/no replay, dynamic new receipt/marker
  binding, wrong native/expired approval, fresh telemetry and 12-minute gate.
- Four tests: binary local bundle preparation with synthetic public receipts,
  exact native/package/scope binding and short-window refusal; no SSH.
- Three Node tests: actual r12 package 15/15 parity and pure final identity,
  admission, route and source gates; no live IPC.
- Seven copied/adapted correlation tests: exact durable Job/source/proof,
  preserved old rows, wrong lineage/fingerprint and actual TAP output identity.
- Python AST, Node syntax and owned-subtree whitespace checks passed.

These checks do not prove production r12 activation, a live canary, current
server/authority/runtime state, durable supervision or native ChatWeb acceptance.
Required live inputs remain the new approval/reopen receipt and fresh current
native receipt. Git remains dirty `main @ 2c554f59...`; this lane wrote only this
new subtree. No SSH/IPC effects, launch, authority mutation, source-product edit,
deployment, service restart, reboot, commit or push occurred.
