# Prepared r10 MCP cold/warm acceptance

Preparation only on dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`. No helper main, MCP command, task, Job, service/runtime operation, authority change, deploy, restart, commit or push was performed in this wave. Source/build remains frozen.

## Scope and guards

The exact approved argv is `node --test tests/control-plane-approved-patch-runtime.test.js`, timeout 300000 ms, output limit 32768 bytes. The default is read-only. `--root-execute` requires a just-reviewed preflight state hash. One deterministic task/action key per cold/warm mode is bound to the fresh r10 epoch, standing context and pilot. An existing task key or exec intent refuses a second attempt. The warm mode also requires the exact successful settled cold attempt. HTTP uncertainty, unknown effect or the 540-second observation deadline never triggers replay, stop, cancellation, deprovision or a new attempt.

The embedded reviewed authority helper has SHA256 `ab182f47b605e5edac1e30cb9cdf48ca53a571f0cbb5367a0f6fb837cbe0c9af`. It verifies the actual Store395 release, service/source/package/schema, target registration/capabilities, grant and preserved historical families. Target is `svhome@100.116.112.22`, service `codex-control-plane.service`, binding `bind_3e05bf64cb3e4bab93d930ae1692bebb`, device `72ceec2d-e3f2-472f-8e3c-99fffe053035`, workspace `workspace_dda1d78e9a21402aa6213f72af64f788`, generation `generation_c2f13e8d02344cf6a38a3f42ecfa59b6`. Credentials remain in protected Ubuntu config/header files and process memory. No credentials or raw command output are emitted.

After an exact settled single-attempt native receipt is proved, supported writer release, task close and exclusively owned temporary context close run in `finally`, including a real terminal test failure or TAP mismatch. A response loss or unproved terminal family leaves the task for root reconciliation without a replay. The helper preserves all prior action/task/intent rows and historical acceptance/quarantine families. It never closes the standing authorized context.

## Fresh public pin document

The root creates a JSON file only from reviewed rollout, renewal, reopening and native-observation receipts. None of these fresh values is guessed or populated by this preparation:

```json
{
  "service_instance_id": "FROM_STORE_ROLLOUT_RECEIPT",
  "activation_epoch_id": "FROM_R10_ACTIVATION_AND_FRESH_HEARTBEAT",
  "process_instance_id": "FROM_FRESH_R10_NATIVE_OBSERVATION",
  "server_instance_id": "FROM_FRESH_R10_NATIVE_OBSERVATION",
  "native_contract_sha256": "FROM_FRESH_R10_NATIVE_OBSERVATION",
  "context_id": "FROM_NEW_60M_RENEWAL_RECEIPT",
  "pilot_id": "FROM_NEW_60M_RENEWAL_RECEIPT",
  "requested_at_ms": 0,
  "expires_at_ms": 0,
  "rollout_receipt_sha256": "SHA256_OF_REVIEWED_ROLLOUT_RECEIPT",
  "native_observation_sha256": "SHA256_OF_REVIEWED_CURRENT_NATIVE_OBSERVATION",
  "facade_contract": {"schema_version": 0, "profile": "FROM_INVENTORY_TOOL_CONTRACT", "sha256": "FROM_INVENTORY_TOOL_CONTRACT"}
}
```

The window must be exactly 3600000 ms with more than ten minutes remaining. Runtime identity must match the fresh ready node; local policy expiry must match the standing context/pilot expiry. Facade contract must equal `inventory.tool_contract`; it is different from native tool contract and target `contract_version`.

Cold/warm names express the root's reviewed phase. The helper does not itself prove whether a VM was cold or reused. Record the corresponding local pre-run manager/host observation and require its reviewed digest in the pin document. Do not infer VM reuse or cleanup from the helper's label or a successful test.

## Root CLI after approval and rollout

Review `static-proof.jsonl` and `prepared-manifest.json` against the exact files before invocation. Run from `E:\Github\Tools-Codex-web`. The pin document contains public metadata only.

```powershell
$canaryPinPath = 'E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r10\mcp-acceptance\pins.root-reviewed.json'
$canaryPinsB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -LiteralPath $canaryPinPath -Raw)))
$canaryHelper = 'E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r10\mcp-acceptance\r10-mcp-canary.py'
Get-Content -LiteralPath $canaryHelper -Raw | ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 svhome@100.116.112.22 python3 -B - --pins-b64 $canaryPinsB64 --mode cold
```

Record and review the emitted `state_sha256`. Only then append `--root-execute --expected-state-sha256 <JUST_REVIEWED_HASH>` to that same cold invocation. Keep its output in a new evidence file and poll the parent command rather than repeating it. For warm, take a fresh local observation/pin document and repeat the separate preflight with `--mode warm`; review its new state hash before the single execution.

The helper's `r10_mcp_canary_complete` proves its central receipt, TAP and cleanup scope. **It is not native Job acceptance.** After each successful central terminal receipt, run the read-only local correlator using the emitted exact IDs/hash:

```powershell
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/verify-r10-native-job.py $canaryPinPath <ACTION_ID> <TASK_ID> <RESPONSE_SHA256> <RAW_OUTPUT_SHA256>
```

Require `r10_native_job_correlated`, `ok=true`, the exact command/Job pair, real terminal root PID, correct owner/runtime/run/wave, and matching raw output hash. Only then declare that mode's MCP canary accepted. The correlator uses journal and canonical ledger read-only and never opens private daemon records. It does not accept the separate pending RUN or prove r10 source/package semantic acceptance on its own.

## Timeout and failure limits

Timeout mode is excluded. The approved test's earlier duration was approximately 5.5 seconds, which cannot guarantee execution lasts at least five seconds. Forced cancellation and invented slow argv are outside this preparation. Successful cold/warm canaries do not prove timeout cleanup.

If terminal proof is unavailable, retain task/action IDs and observe/reconcile the original action. Do not manually release a writer or close context while effect is uncertain. For a proved settled family whose transport interrupted cleanup, root may use the supported `task_control writer_release`, then `workspace_context task_close` under the same principal. Closing a temporary context additionally requires the exact owner/binding/created time/expiry and sole-action/no-grant guards in `cleanup_family`; never close the standing context. Do not rerun this helper's execution as cleanup.

## Prepared proof

`check-prepared-canary.py` checks syntax and ten pure pin/key/TAP cases, embedded reviewed source digest, exact mode keys and absence of the old `exec_stop` fallback. The focused schema review confirmed task-open idempotency is in `mcp_task_open_idempotency`, writer renewal keeps its generation, `exec_status.exec` omits native identity, and bounded output adds a 19-byte display wrapper. No live proof was produced by these tests. Next action is root review and the grouped approval/rollout boundary already pending.
