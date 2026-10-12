# Read-only assessment: r9 owned cleanup through a new cancelled Job

No execution, cancellation, VM operation, service operation or authority mutation was performed for this assessment.

## What the serving package supports

The r9 packaged `session_control.py`, `processes.py` and `protocol.py` are byte-identical to the current source examined. Their packaged SHA256 values are:

- `session_control.py`: `b923407705d9c18cf83de45381832ee58250c414aa09f8a9fe6b2ea42d6814ce`
- `processes.py`: `a7578dced89bd0c401ab1583a305bea5c5b58b3cc0c054ef1528d89847310365`
- `protocol.py`: `1b62a0e66ebbcd88d3a0f79973224f912fae3e1fa67aab1c028da4814d8cd620`

The packaged `exec_tools.py` per-command closure sets abort when the session timed out, was explicitly marked `sandbox_abort_on_cleanup`, or ended by signal. The packaged state-aware manager's `release(abort=True)` invokes `_deprovision_id(self._active.sandbox_id)` and clears `_active` only after the exact deprovision succeeds. This operates through the manager that acquired the new command's lease and does not require discovering/adopting a VM from host process names.

`command_control` uses `action=kill`, not `stop`. It resolves the command handle and calls `kill_session`. Only if `process.poll() is None` does it set `sandbox_abort_on_cleanup=True` before terminating that command's owned process group. It waits `wait_ms` (default 3 seconds through command_control), may escalate within that owned process tree, then formats terminal output, which runs per-command cleanup.

## Why ordinary central exec_stop is insufficient for this test

The central Recovery exec bridge hardcodes native initial `yield_time_ms=min(30000, timeout_ms)`. The previously approved exact test command finishes in about 5.5 seconds. Therefore the node normally receives native command/Job identifiers after the test has already exited and completed normal warm-manager release. A stop request against a settled action is acknowledged without marking an abort and leaves the warm VM running. Stateless MCP 2026 explicitly rejects `notifications/cancelled`; that notification cannot interrupt the current stateless request through its normal protocol.

## Smallest conditional procedure

**Operational decision:** The conditional native `yield_time_ms=0` route below was not selected. The production attestation secret is ephemeral in RecoveryHost memory and is not exposed through the supported credential APIs. Reading process memory or environment to recover it is prohibited. No mixed notification cancellation workaround is being developed or used. The prepared alternative uses one distinct central `exec_run` with the same approved argv and a 5000 ms timeout, and requires an exact timeout Job plus two fresh host/daemon absence observations. A natural completion is preserved without retry or a VM-cleanup claim.

The owner controller can prepare a distinct, audited local canary using the existing authenticated and attested native tool boundary, if that route is authorized within the exact current workspace and permission window. It must not silently bypass server policy or reuse a settled action/idempotency key.

1. Pin current r9 epoch/process/server identity and exact `E:\Github\Tools-Codex-web` registration/generation. Record zero active/starting commands and Jobs, preserve original acceptance and quarantine families, and prevent unrelated intake during the controlled check.
2. Bind a fresh task context to that exact registered workspace. Use a new idempotency key and the already approved argv `node --test tests/control-plane-approved-patch-runtime.test.js`; set native `yield_time_ms=0`, keeping the existing bounded timeout and output limit. The normal central bridge does not expose this initial-yield option.
3. Require returned `status=running`, exact nonempty `command_id` and `execution_owner.job_id`, and unchanged current runtime identity. Cross-check that exact durable Job pair and root process identity. Promptly call `command_control` with `action=kill`, the exact command handle, `signal=TERM`, `wait_ms=3000`, under the same authenticated controller/context. Never select a process by PID alone.
4. If the Job already exited before kill, the abort path was not taken. Classify the attempt accordingly and retain the warm runtime. Do not declare cleanup or stop the native process, and do not replay previous settled canaries.
5. Retain the distinct kill response and the exact Job terminal observation. Independently observe no Windows Sandbox host processes (including `vmmemWindowsSandbox`) and no live daemon record in two fresh observations, plus zero active/starting command/Job state, before treating the old runtime as free of a warm VM. Never print the daemon nonce or other private fields.

The kill request may synchronously wait through the existing deprovision phase (up to 210 seconds) after the command termination wait. A one-shot helper must respect that known bound and retain output asynchronously; changing general production deadlines is not justified. A transport timeout does not undo cancellation or prove failed cleanup. Preserve the outcome and observe, without replay.

## Proof limits

r9 exposes no `cleanup_confirmed` result or durable Sandbox-cleanup receipt. `ExecSession.cleanup_sandbox_state` removes its callback before running it; a watchdog may own that callback concurrently. Its failures become session warnings, sometimes after an earlier snapshot. `_complete_session` records `process_tree_cleaned=True` regardless of whether Sandbox teardown was confirmed. The central relay also does not carry session warnings as cleanup evidence.

On Windows the durable Job may record `exited` even after explicit kill because Windows process exit codes are positive and `refresh_status` clears `terminating`; retain `killed=true`/terminal kill response separately. Neither the durable terminal state nor the central stopped receipt alone establishes VM disappearance.

Thus controlled cancellation is a supported exact-owned cleanup mechanism, but operational success remains conditional on catching the distinct command while running and observing the final host/daemon quiescence. This assessment does not prove that live transition or authorize any additional operation.
