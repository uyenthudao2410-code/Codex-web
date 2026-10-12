# r7 canary diagnosis — 11 October 2026

Read-only diagnosis of action `act_2673b93c5bb3483889742dfe3055fd3d`,
task `task_8982097843784d44bcc4bb0440c35141`, attempt
`try_2a6dece218e641eaa50de19cf024085e`.

## Proven local outcome

- The original node journal records `unknown`, submitted, with bridge diagnostic
  `CONTROL_PLANE_EXEC_MCP_REJECTED`. This is a semantic MCP failure response,
  not the recorded code for an IPC or HTTP timeout.
- Deriving the native idempotency key from the exact journal request yields
  `cpex_00404f34a676c9e63c90780cac8a0ce1593e9962acd9d97c7e150150`.
  Its canonical record is `exec_command / unknown / SANDBOX_STATE_PHASE_FAILED`,
  from 10:25:02.638Z to 10:27:09.075Z.
- Exact Job `8f6df428efb4489aa310f6266cce054f`, command
  `WaJumSgZyYU90Yj_Mt7qu-Gp`, is `spawn_failed`; root PID is zero and root
  process token is empty. It finished at 10:27:08.489Z. This is failure before
  the managed test process was bound. No test exit code or output was proved.
- At preparation 10:31:22Z, there were zero active managed Jobs and zero live
  `wxc-exec.exe`, daemon, guest, WindowsSandbox, WindowsSandboxClient and
  WindowsSandboxServer processes. The immutable pending acceptance run remains
  separate from this canary.

## Timeout hypothesis

`electron/services/recoveryIpc.js` uses the supplied timeout through
`Math.max(100, ...)`; it has no 120-second maximum clamp. The r7 startup budgets
are still 300 seconds local HTTP, 330 seconds Recovery IPC, and 360 seconds node
subprocess. The native failure completed well before those deadlines.

`windows_mxc_state_aware.py` emits `SANDBOX_STATE_PHASE_FAILED` for failure to
launch a lifecycle envelope or a nonzero lifecycle backend response. Its Python
start-phase limit is 210 seconds. The observed 126-second Job duration alone
does not identify the backend cause or failed phase.

## Diagnostic gap

The native idempotency summary retained only `category`, `error_code`, and
`outcome_unknown`; it did not retain `phase` or `backend_error_code`. Recovery's
local MCP adapter also converts the structured native error to generic
`CONTROL_PLANE_EXEC_MCP_REJECTED`. The matching Recovery log confirms that
generic code. No arbitrary logs, sealed arguments, credentials, or nonce bytes
were emitted during diagnosis.

The next code repair should preserve the native error code and allowlisted
phase/backend code through this existing response path, and durably record
those fields beside the exact Job/idempotency record. A further live attempt
requires root's explicit controlled validation decision; replaying the original
UNKNOWN action would not reveal its lost evidence.

## Supported reconciliation

`reconcile-r7-canary.py` adapts the existing r4 exact terminal-receipt procedure.
Default execution proves the journal/request correlation, terminal native Job,
empty root identity, zero active resources, and pinned packaged node agent.
Only `--submit --operator-approved` submits a terminal failed receipt through
the existing `_submit_receipt` API. It never executes a command or writes the
original node journal or canonical ledger.

Root submitted at 10:31:51Z. The server acknowledged receipt
`rcpt_97a6b0ffb80149fd8f87c5d6b70e3182` as **failed / settled / replayed=false**.
The original journal SHA-256 remains
`c915895a5acb145373d56bc8c4bd1e17bf01ddb507c40caff95f148986ca4461`.
Exact task/writer closure is a separate server checkpoint owned by root.
