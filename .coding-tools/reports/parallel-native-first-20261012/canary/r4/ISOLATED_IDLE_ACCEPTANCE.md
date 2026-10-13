# r4 one trusted isolated command and automatic idle retirement

These dated helpers do not alter application source or require a rebuild. Root
coordinates every live operation. Preparation and the offline tests do not run a
VM, an execution action, or a policy install.

## Preconditions

- Current Windows r4 candidate has exact source/package parity and isolated smoke.
- Current Recovery Host has the exact READY/open epoch and no active local jobs.
- Both workspace policies are enabled and scoped by exact ID/generation.
- Native canaries are finished and their temporary approvals have been restored
  using the reviewed final-policy helper. Codex-web begins in `native_first`.
- Fresh two-root READY pins remain bound to the same Ubuntu service, principal,
  grant, facade, node identity, exact workspace scopes and quarantined history.
  Their purpose is `isolated-idle`, with Codex-web's exact isolated policy hash
  and AutoCAD in `native_first`; native fixture approvals are not reused.
  Pin the independently generated launcher `supervisor_instance_id`, native PID
  and Win32 start token from current local state. The launcher's instance ID and
  the MCP `process_instance_id` are separate identities.
- No Sandbox host or active daemon exists before the observer starts. Historical
  orphaned records are neither authority to stop a VM nor rewritten evidence.

## Run sequence

Run the selected packaged `Coding Tools MCP.exe` under `ELECTRON_RUN_AS_NODE=1`
with the `sandbox-idle-policy.cjs` helper. Use absolute current candidate
`--parity-proof` and `--smoke-proof` paths for each operation.

1. `prepare --output <new absolute plan JSON>` observes exact scopes, epoch and
   idle census. It saves both safe policy observations, original native prefixes
   and the canonical hash of the complete AutoCAD policy scope.
2. `isolate --apply --plan <plan JSON>` installs isolated mode for Codex-web only,
   with the saved native prefixes and `probeSandbox=false`. It saves an intent
   before installation, verifies the resulting policy, and proves AutoCAD's scope
   unchanged. On uncertain install failure, inspect the intent/current policy;
   do not repeat the mutation from a generic failure result.
3. Execute `invoke-isolated-idle-canary.ps1` with:
   - `-ExecuteConfirmedIsolatedIdleCanary`
   - `-ReadyPinsPath <fresh two-root pins>`
   - `-ParityProofPath <current parity>`
   - `-IsolatedPolicyReceiptPath <isolate result>`
   - `-PythonPath <absolute local Python with psutil>`
   - `-AttemptId <new UUID>`

   The wrapper starts a hidden read-only Windows sampler and waits for its ready
   signal before SSH dispatch. The remote helper sends exactly one trusted
   `argv=["node","--version"]` action through the shared facade. Secrets remain
   on Ubuntu. Original task/action/Job handles are recovered after response loss;
   no lane is redispatched, and UNKNOWN effects defer cleanup.
4. Root reviews the remote terminal proof and Windows observation report.
5. After the exact original action is settled and canonical work is idle,
   `restore --apply --plan <plan JSON> --isolated-receipt <isolate result>
   --remote-receipt <original remote NDJSON>` restores
   Codex-web's saved mode/prefixes. It rejects changed scope or unexpected current
   policy, requires the original remote action settled with task/writer cleanup,
   and again proves AutoCAD scope unchanged. UNKNOWN defers restoration until the
   original is reconciled. If the wrapper failed before any dispatch, root must
   review that distinct state before restoring through a supported policy API.
   Failure of idle acceptance
   does not authorize a VM stop, generic process kill or repeated exec.

## Acceptance evidence

The remote terminal receipt must show exit 0, Node version output, one delivery
attempt, stable Job/command/local handles, exact actor/runtime/facade/task/lease,
and `isolated / hypervisor / isolated_preferred` routing metadata.

The sampler must observe a warm VM with exactly one writable Codex-web mapping,
the pinned packaged daemon and exact Win32 FILETIME identities for its VM hosts.
It then observes automatic disappearance of that record, daemon and original
hosts without a lifecycle command and with the same READY MCP PID/epoch. A
Sandbox-named `vmmemWindowsSandbox`/`vmmemWSB` memory aggregate must also be absent
for the RAM acceptance result. Other kernel aggregates are reported separately
and carry no ownership or termination authority.

Idle timer is 30 seconds after durable terminal Job observation. Deprovision has
a separate 210-second bound; the sampler permits 270 seconds after the remote
terminal observation. Repeated terminal receipt reads do not extend the timer.
Warm-to-exit below 25 seconds is rejected as too early/externally interrupted.

There is no dedicated idle teardown receipt in the current source. Report the
actual correlated receipt/record/process/RAM evidence and its capture window;
do not claim a provider billing measurement or a general performance benchmark.

## Offline proof

`python -B test-isolated-idle-canary.py` passes four boundaries: one dispatch,
lost-response recovery without redispatch, UNKNOWN cleanup deferral without stop,
and rejection of a native receipt as isolated acceptance. Python AST, JavaScript
syntax and PowerShell parser checks passed. Live Sandbox acceptance remains
pending until root executes and reviews these outputs.

