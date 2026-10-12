# Owned warm executor cleanup — source proof

Observed repository: `E:\Github\Tools-Codex-web`, dirty `main` at `2c554f59cb7b8ffc86ce5e0e28076c792777642f`, 2026-10-11 Asia/Saigon.

## Implemented boundary

Authenticated existing `POST /__control/activation` with `action=prepare` retains all existing workspace, active/starting command, managed Job, tool call, background work, lifecycle, acceptance and checkpoint checks. Once quiescent, it establishes the ordinary activation fence and starts one asynchronous close of the Runtime's exact owned Windows Sandbox manager. The HTTP response returns immediately with `safe=false`, `SANDBOX_CLEANUP_PENDING`, and content-free exact operation/process/server/workspace correlation. The worker never holds `activation_lock` during backend teardown.

The ordinary prepare expiry still must be within 60 seconds. Repeated prepare calls for the same operation refresh only that fence, retaining the original cleanup deadline (430 seconds: the existing close bound of a 215-second lease wait plus 210-second deprovision phase, with 5 seconds of scheduling allowance). The cleanup barrier remains authoritative after fence expiry and guards both HTTP tool admission and direct exec starting-slot admission. Pending cancellation is refused; teardown failure or deadline expiry remains fail-closed. A late thread cannot convert deadline failure to success.

A closed manager reference is discarded only when `close()` returned literal `True` and the Runtime still refers to that exact object. A subsequent prepare reruns canonical preflight and requires a fresh fence. Cancel after confirmed cleanup allows ordinary execution to create a fresh manager. No-manager prepare success explicitly reports `executor_cleanup={state:not_required,confirmed:true}`; successful cleanup reports completed/confirmed. Read-only GET preflight never starts teardown. GET and prepare advertise `executor_cleanup_supported=true` to prevent an older runtime from being mistaken for cleanup-capable.

No authentication, schema, ownership, sandbox policy, or acceptance gate was relaxed. Native binaries and backend lifecycle deadlines were unchanged.

## Validation

Command from `resources/coding-tools-mcp`:

```text
node ../../scripts/run-python.js --module pytest tests/test_activation_executor_cleanup.py tests/test_activation_preflight.py tests/test_windows_mxc_state_aware.py tests/test_exec_spawn_failure.py -q
72 passed in 47.85s
```

The dedicated 13-test cleanup suite covers bounded pending HTTP 409, unauthorized requests, active/starting command guards, fixed cleanup identity/deadline, expired fence barriers, direct exec refusal before spawn, exact operation ownership, confirmed manager disposal, cancellation/resumption, failed cleanup, late completion after deadline, replacement-manager preservation, read-only observation, explicit no-manager proof, and exact-owned deprovision with bounded lease wait.

`python resources/coding-tools-mcp/scripts/check_module_size.py`: passed.

Scoped `git diff --check`: passed (Git emitted existing LF/CRLF advisory messages, no whitespace failure).

## Frozen source identities

| Repository path | SHA256 |
| --- | --- |
| `resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py` | `418412577d57134b06b67baa8107c04f572a81ea4279f059bbb3bef6cbc4334e` |
| `resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py` | `08868cf7679a70162ac3b38121b1629fabb4505da0bf1fab2a77d7d4c3924309` |
| `resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py` | `fd218393a555d3bc0aa324e00587c06461a83aca33977dace4f0fa60c5b7a401` |
| `resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py` | `ca2ab4d58b3865a67773c3cb64657f181a37eb1cf863ce45e273e13c82184f6e` |
| `resources/coding-tools-mcp/tests/test_activation_executor_cleanup.py` | `cb7758a3bcc1a92dbcec399e2eeb57670211beac06fccb7b6e61f57fefae2e0e` |

These hashes cover prior retained edits plus this repair. No prior dirty source was reverted.

## Coverage limits and old r9 transition

This is source/deterministic proof for authenticated prepare and admission; actual packaged activation and live owned-VM teardown are separate evidence gates. Ordinary `nativeService.stop`/`RuntimeOrchestrator.stop` paths that skip prepare are not made safe by this native patch alone. The parent controller is adding full-clean prepare polling and preserving a pending/failed cleanup boundary instead of forcing native shutdown.

The serving r9 predates the cleanup marker/control. Its existing backend supports an exact `wxc-exec --experimental --config-base64` deprovision phase by `sandboxId`; the backend uses the private daemon record nonce, daemon PID plus creation time, and immutable mapped-folder record to authenticate owned cleanup. The retained native Job/action receipts do not expose `sandboxId`, and r9 has no authenticated manager-state/close operation. A mapped workspace alone does not prove that the VM belongs to this exact Runtime. Therefore this worker performed no external deprovision, IPC stop, process kill, HCS cleanup, runtime activation, service change, or deployment. The old-runtime migration needs exact owned-sandbox correlation evidence and explicit operational handling before replacement can be called safe.

No commit, push, tag, release, restart, reboot, or runtime Job was created by this repair. All delegated test sessions finished exit 0.
