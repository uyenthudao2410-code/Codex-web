# One new r14 MCP edit → test → proof canary

Preparation only. Root executes this packet after explicit r14 approval, exact r14 READY activation, supported old owned Sandbox cleanup, and same-window pilot replacement/reopen. No current fixture, checker, runtime, server or authority has been changed by preparing this packet. No checker/test has been run.

## Exact proposed effect

Target `tests/fixtures/initial-proof-canary-target.cjs` is currently the old successful patch POST (`d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e`). Change only `if (['passed'].includes(proofStatus))` to `if (proofStatus === 'passed')`, producing 406 bytes / SHA `0ae4bfe07e94d171e8885a464f3bf8f3e0d9b49a444b144b1aed2e4963ab4496`. Patch SHA `4abb1d97a6da4ac507c70b0af1e1902160609597e3efe4096c6a8d96b19cb9b2`.

The existing four-case checker stays byte-identical (`059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230`). Verification is exactly structured argv `node --test tests/fixtures/initial-proof-canary-check.cjs`, workspace cwd, timeout 60000 ms and max output 32768 bytes; plan SHA `235ecd2dc1bf8b49b21648ffd24df378088916e65e2420cb383fa79a6439afe7`. Both pre/post expressions have the same intended behavior. This canary checks the new cold Sandbox edit→test→proof transport, not a new application bug fix.

Use the distinct `r14_same_window-initial-*` idempotency namespace and remote operation dir `/home/svhome/.local/state/codex-control-plane/owner-operations/r14-same-window-activation/canary`. Never reset the target, delete an old intent, reuse the old POST, retry the old action or accept its RUN/WAVE.

Existing context remains `ctx_1e7e2fec6f0e43018db7a51c6980e5c2`; requested time 1791758571067, expiry 1791776571067. The new pilot must come from the actual same-principal/binding/expiry r14 reopen. Prior two RUN/WAVE hashes must be unchanged. Candidate r14 source/build proof remains unchanged.

## Root sequence

1. After r14 activation/reopen, run `node native-preflight.cjs`. This authenticates the exact current r14 host/native epoch, validates the frozen package, actual target/checker and both pending row hashes, reads canonical census and proves 0 active Jobs and 0 Sandbox/backend processes. It constructs no Sandbox manager. The cold-VM preflight is required.
2. Obtain a fresh real server observation with `phase=r14_same_window_read_only_observation`, `next_phase=intake_reopened`, actual future r14 `approval_id`, native echo fields, principal ID and `next_marker_sha256` for `authority-transition-public.json`. Use `node make-pins.cjs --native-preflight=ABS --native-preflight-sha256=SHA --authority-receipt=ABS --authority-receipt-sha256=SHA --approval=ABS --approval-sha256=SHA`. It writes an exclusive pins file. Neither old runtime/pilot IDs nor placeholder pins are accepted.
3. With portable Python, run `root-canary-ssh.py prepare --pins=ABS --native-preflight=ABS --expected-native-preflight-sha256=SHA --authority-receipt=ABS --expected-authority-receipt-sha256=SHA`. It creates a reviewed/pinned local SSH bundle using retained exact common/SSH helpers. Use the returned staging manifest for `stage --manifest=ABS --execute`, `preflight --manifest=ABS --execute`, then exactly one `dispatch --manifest=ABS --execute`. Review their real receipts; no automatic replay is allowed.
4. Observe that same new action with `observe --manifest=ABS --execute`. During cold provisioning, poll read-only observation at sensible intervals (around 10–15 seconds), preserving its actual action/task identity. Never issue another dispatch after timeout, unknown effect or receipt loss. Preserve any applied target if proof fails; classify the exact failure and leave acceptance pending.
5. When passed settled proof is observed, run the prepared read-only `correlate_r14_same_window.py --receipt=ABS_NEW_SETTLED_RECEIPT --receipt-sha256=SHA --pins=ABS_LIVE_PINS --pins-sha256=SHA`. It checks the actual bridge journal, source-bound original proof, terminal command/Job, postimage/checker and both old pending records. Its result provides the actual native Job `completed_at_ms`. Keep source/docs frozen through these reads and output capture; `.coding-tools` evidence is excluded from the source fingerprint.
6. Capture output immediately before its 300-second in-memory retention expires. Use the exact completion timestamp from native Job evidence; a late observation timestamp is not proof that old output is still retained. Invoke the output reader below before cleanup/other diagnostics, then run the same correlator with `--output-receipt=ABS --output-receipt-sha256=SHA` to bind its TAP to that original proof. Failed/timed-out proof is preserved for diagnosis; this passed-proof correlator never treats it as a pass. After capture and exact proof correlation, `cleanup --manifest=ABS --execute` releases/closes only this new central task. It does not perform semantic acceptance.

## Supported output and its limits

Control Plane `command_control exec_output` is only implemented for central exec actions. It cannot read an approved-patch initial-proof Job. Recovery IPC exposes no general arbitrary-command read method. The prepared fallback therefore uses the supported native MCP `command_control` read/poll surfaces through a tiny separate Electron app. It uses the pinned developer Electron binary and explicit app directory, without product bootstrap, windows, native starts or the product's single-instance handler. Its userData/sessionData are under this evidence directory, separate from the Desktop profile lock.

The app reads `SecretStore` for the existing `web-mcp-assistant` profile into memory, authenticates current r14 `/__control/health`, binds the exact command/Job pair through zero-yield poll, then captures retained stdout/stderr by output_ref. It does not grant authority, forward credentials in argv/env/files, or change local policy. It rejects private output, truncation/drops/eviction, output over 32768 total bytes, mismatched health/Job identity and output older than 300 seconds. Each HTTP request is bounded to 10 seconds; the app has a 26-second watchdog and root runner a 30-second child bound. No diagnostic stderr/raw untrusted stdout is emitted.

```text
node root-capture.cjs --capture-new-canary-output
  --manifest-sha256=ACTUAL_CANARY_HELPER_MANIFEST_SHA
  --observation=ABS_NEW_SETTLED_CANARY_RECEIPT --observation-sha256=SHA
  --pins=ABS_ACTUAL_LIVE_PINS --pins-sha256=SHA
  --completed-at-ms=ACTUAL_NATIVE_COMMAND_COMPLETION_MS
```

The runner saves an exclusive `native-output-TIMESTAMP.json`; for passed proof, it requires actual exit 0, empty stderr and each of the four named TAP assertions plus `tests 4 / pass 4 / fail 0`. Failed/timed-out proof can retain its exact output if a command/Job pair is available, without claiming TAP passed. Missing command IDs, expired/evicted output, a hung reader, incomplete streams or unverifiable identity are explicit capture gaps. Do not rerun the checker/canary to fill a gap, and do not claim four actual TAP assertions from exit zero or proof metadata alone. The r13 output gap remains unchanged.

Semantic acceptance stays pending for the real authorized controller. Helpers have only received syntax/static review during preparation; live transport/cold Sandbox/output capture are not proven until root executes the newly approved canary.
