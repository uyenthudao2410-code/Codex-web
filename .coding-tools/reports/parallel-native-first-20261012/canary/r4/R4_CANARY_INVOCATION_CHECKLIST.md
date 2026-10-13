# r4 canary invocation checklist

Additive preparation only. All r3 helpers and receipts remain unchanged by this
lane. Expected candidate:

`E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4\win-unpacked`

Before invoking, root must verify fresh r4 parity/smoke, exact READY/open epoch,
Ubuntu service readiness/current scopes, historical UNKNOWN preservation and
current policies. Use fresh r4 runtime pins. Original r3 canary failures remain
evidence; an uncertain action must be reconciled before starting another task.

## 1. Offline fixture reuse receipt

The existing fixture remains history. This command checks original seed hashes,
absence of build artifact and the copied reviewed harness. It writes only a new
reuse receipt, with `mutations: 0` and no shared-MCP creation claim:

```powershell
$r4 = 'E:\DEV\Codex-web\.coding-tools\reports\parallel-native-first-20261012\canary\r4'
$manifest = 'E:\DEV\Codex-web\.coding-tools\reports\parallel-native-first-20261012\canary\fixture-preparation.json'
$reuse = Join-Path $r4 'fixture-reuse-r4.json'
python -B (Join-Path $r4 'prepare-r4-fixture-reuse.py') --manifest $manifest --output $reuse
```

Changed seed bytes, an existing build artifact or mismatched harness prevent
reuse. Preserve the original manifest and the additive reuse receipt.
An already captured r4 receipt such as `fixture-reuse-179181.json` may be used
instead when its manifest and harness hashes match these exact inputs.

## 2. Full Codex-web canary

Install only the exact reviewed Node build prefix on the current generation.
Capture fresh server readiness and build-policy receipt, then construct new
r4 Codex pins using `prepare-reviewed-canary-pins.py` in this directory with
the original fixture manifest. The builder must verify the current epoch,
node heartbeat, binding/generation/pilot, source/contract and policy digest.

```powershell
$pins = 'ABS_FRESH_R4_CODEX_PINS_JSON'
$parity = 'E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-candidate-parity.json'
$smoke = 'E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-packaged-smoke.json'
& (Join-Path $r4 'invoke-native-first-canary.ps1') -ExecuteConfirmedReadyPilot `
  -ReadyPinsPath $pins -ParityProofPath $parity -SmokeProofPath $smoke `
  -FixtureManifestPath $manifest -FixtureReuseReceiptPath $reuse -AttemptId (New-Guid) `
  -IncludeApprovedBuild
```

Require exactly 100 reads, 20 guarded patches, 20 exact readbacks, 10 distinct
Node Jobs, 3 Git Jobs, approved Node build/artifact readback, original task
closure and writer release. Native Jobs must retain `native / process_container`
routing metadata. Preserve final receipt, original actions and intent records.
On response loss, observe original handles; do not dispatch the attempt again.

## 3. Two-root overlap

Prepare fresh overlap fixtures/manifest linked to these r4 copied harness
hashes and exact root HEADs. Install the narrow hold-script prefixes on both
current generations. Capture new readiness/approval receipts and overlap pins.
Use `invoke-parallel-overlap-canary.ps1` in this directory with the new pins
and original additive overlap fixture manifest. Require two distinct tasks,
writer leases and Jobs, positive same-node Job interval intersection, exact
per-root File API effects, client reconnect without redispatch, terminal tasks
and preserved historical UNKNOWN evidence. Client reconnect does not prove a
runtime restart.

## 4. Local semantic acceptance and idle

The r4 semantic helper pins only the r4 candidate, actual runtime identity and
reviewed stock normal Electron operator process. Follow
`SEMANTIC_OPERATOR_COMMANDS.md`; proof-less original waves must be truthfully
rejected, reported and acknowledged before same-RUN proof-only replan. Never
reapply patches or import proof from another RUN.

Restore final `native_first` policies and capture their receipt before idle
testing. Follow `ISOLATED_IDLE_ACCEPTANCE.md` in this directory. r4 idle pins
must show `purpose: isolated-idle`, Codex-web `isolated`, AutoCAD `native_first`,
actual policy digests and separate native launcher supervisor/PID/start token
fields. The observer starts no VM and stops no process. Restore Codex-web's
original saved policy only after its original isolated action is settled.

## Final evidence

Run `aggregate-production-evidence.py` in this directory with the actual r4
receipts and a new output path. Missing inputs remain `null`; it creates no
acceptance. Root then updates maintained product docs using measured outcomes,
final policy/readiness/source state, canonical job census and Git state. Full
production completion must not be inferred from package creation or READY.
