# Post-reboot r5 live test checkpoint — 11-10-2026

## Outcome

The owner completed Windows reboot at 15:42:38.500 +07 and subsequently
authorized r5 activation and testing for the same workspace and expiry.
The exact workspace is `E:/Github/Tools-Codex-web`, binding
`bind_3e05bf64cb3e4bab93d930ae1692bebb`, profile `web-mcp-assistant` on
DaoChienThang. Context/pilot/standing authority still expires at
**16:26:24.008 +07**; no extension was inferred.

r5 is active at
`dist/windows-candidate-mxc-wsb-cbe1774-exec-coldstart-1011-r5/win-unpacked`.
READY/admission proof passed at 16:16:02 and again at 16:18:48.695. Exact Host
1936, UI 852, Coding MCP 9632 and connected agent 10336 identities match the
candidate. Pending local acceptance was preserved through supported activation.

The authenticated Ubuntu MCP → Windows Recovery IPC → Windows Sandbox test
completed at 16:16:56 with **4 PASS / 0 FAIL / exit 0**:

```text
node --test tests/control-plane-approved-patch-runtime.test.js
```

Action `act_2de8172636ef4cdba9e388c203855f6b` has one attempt and a settled
completed receipt. The 1,089-byte tool output has SHA-256
`f928c0f86cc5fc728424a8891ad724c938e9de08443fc626f97b82982eac7b7d`.
Task `task_9cfe9f74f92e476982085da7165ea0d8` and its writer were closed.
Final read-only native observation at 16:19:30.872 confirms exact Job
`21eeffeec3b1411daed1219ebaa5778e` exited with code 0 and **zero active managed
jobs**. Tool-rendered TAP byte length and native captured-output byte length
are distinct representations; the tool receipt hash is the live test oracle.

## Changed boundary and validation

The timeout repair affects `electron/services/runtimeOrchestrator.js`,
`control-plane/control_plane/recovery_exec_bridge.cjs` and
`control-plane/control_plane/node_agent.py`, plus their three focused test
files. Initial cold-start budgets are now 300 s HTTP / 330 s IPC / 360 s node
adapter. Poll/stop retain short budgets; poll yield reserves 10 s for transport.
Authentication, schema, policy, sandbox and UNKNOWN/no-replay gates remain.
Thirteen focused checks, exact source/package parity and packaged smoke passed
before activation; the new live test supplies separate execution evidence.
Current guidance was updated in `docs/CURRENT_STATE.md`, `docs/TESTING.md` and
`docs/MCP_WEB_OPERATIONS.md` with the supported test sequence.

## Failure classification and external state

The first r4 test reached a bridge timeout; its native Job subsequently failed
Sandbox startup before a process existed. Independent exact evidence was
submitted through the supported receipt API to settle the action failed.
The original UNKNOWN journal/receipt was preserved and no replay occurred.
The exact underlying Sandbox backend error was not retained; the successful
r5 test does not prove that every transient VM startup failure is eliminated.

Final Ubuntu observation at 16:17:36.644 reports online/ready/dispatchable,
enabled policy, zero queued/accepted actions, zero open tasks/writers, and the
unchanged historical 13 unresolved-action digest. Ubuntu remains at revision
`beaa9d5ade4926ef231e3ec9d0a517fe93830e90`, PID 794023, schema 28, with all 38
release files verified. This continuation activated/restarted Windows runtime;
it did not deploy/restart Ubuntu, renew authority or reboot Windows again.

## Git, remaining work and next action

Primary remains dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f` with
pre-existing edits preserved. No primary commit, push, tag or public release
occurred. Local RUN `95e909f0040a448faa9f1f3257e2ee2c` / WAVE
`c101beadfc6d4f2fbc13845052c84693` remains acceptance-pending, independently
of the closed central test task. No semantic acceptance was fabricated.

Remaining proof gates include actual ChatGPT client discovery/invocation,
a new live write with central-to-local semantic acceptance, artifact acceptance,
directory listing and whole-suite coverage. Next operator action: refresh the
ChatGPT connector discovery, select the exact Tools-Codex-web binding, obtain
the current inventory contract and follow the test sequence in
`docs/MCP_WEB_OPERATIONS.md` while authority is valid. Expired authority needs
an owner-approved renewal before another protected live operation.

Receipts: `postreboot-runtime.r5-activation.jsonl`,
`postreboot-exec-r5-verification.jsonl`, `ubuntu-postreboot-server-final.jsonl`.
