# r4 local semantic operator helper

Prepared helper only; no production call was performed by its author. The
read067 UNKNOWN attempt did not create patch waves and cannot pass these
mutation gates. First settle the original action through supported evidence,
then complete a separately authorized full canary with 20 exact patches and
readbacks, an approved build, original task closure and writer release.

## Reviewed bytes

- `local-semantic-acceptance.cjs` SHA256:
  `d91694fc8dc0c4a79d458917f6a235e01cc0d4ffa8c5312d806ef03c4e90101d`.
- `prepared-verify-postimages.cjs` SHA256:
  `a92245b8502e4693cd67bd748366147bcae00464e91e1758c5b638d49cb1d848`.
- Stock operator Electron `E:/DEV/Codex-web/node_modules/electron/dist/electron.exe`
  SHA256: `8593db40c0c6e5e3c4b6b0a225b1dc9a549ecdf10f6cf2010cf5b6ce869ce07f`.

Six offline helper tests passed. The independent isolated Runtime check proved
that rejection's returned report latch can be stale and that public
`agent_workflow` rejects `timeout_ms`; the helper uses fresh audit latch and
supported `timeout_seconds=60`. Production semantic acceptance remains pending.

## Exact inputs and offline preparation

The operator supplies a successful final canary NDJSON path and its current
digest. Freeze these inputs before starting; an uncertain receipt is never a
reason to repeat a mutation.

```powershell
$semanticRoot = 'E:\DEV\Codex-web\.coding-tools\reports\parallel-native-first-20261012\canary\r4'
$semanticHelper = Join-Path $semanticRoot 'local-semantic-acceptance.cjs'
$semanticHelperHash = 'd91694fc8dc0c4a79d458917f6a235e01cc0d4ffa8c5312d806ef03c4e90101d'
$semanticVerifierHash = 'a92245b8502e4693cd67bd748366147bcae00464e91e1758c5b638d49cb1d848'
$semanticPins = Join-Path $semanticRoot 'codex-ready-pins-r4.json'
$semanticCanary = 'ABS_SUCCESSFUL_FINAL_CANARY_NDJSON'
$semanticPinsHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $semanticPins).Hash.ToLowerInvariant()
$semanticCanaryHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $semanticCanary).Hash.ToLowerInvariant()
$semanticInputs = @('--helper-sha256', $semanticHelperHash, '--pins', $semanticPins, '--pins-sha256', $semanticPinsHash, '--canary', $semanticCanary, '--canary-sha256', $semanticCanaryHash)
node $semanticHelper prepare @semanticInputs
node $semanticHelper prepare-verifier @semanticInputs --prepare-fixture --verifier-sha256 $semanticVerifierHash
```

`prepare-verifier` exclusively creates
`tests/fixtures/native-first-canary/verify-postimages.cjs`, hashes the readback,
and writes a preparation receipt. It refuses existing output, changed source,
missing postimages or an unsuccessful/unsettled canary. It runs no API or
verifier. Retain that receipt before proceeding.

## Normal Electron launch

Run the stock executable in normal Electron mode, using this script as its main
module and an isolated operator profile. It starts no product main/UI, reads
the installed profile's bearer into memory through the reviewed candidate
SecretStore, and calls the local authenticated MCP API. It uses an explicit
Electron operator identity and claims no connector/ChatWeb attestation.

```powershell
$semanticExe = 'E:\DEV\Codex-web\node_modules\electron\dist\electron.exe'
$semanticProfile = Join-Path $semanticRoot 'semantic-operator-profile'
$semanticParity = 'E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-candidate-parity.json'
$semanticSmoke = 'E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-packaged-smoke.json'
$semanticLiveInputs = @($semanticInputs) + @('--operator-exe-sha256', '8593db40c0c6e5e3c4b6b0a225b1dc9a549ecdf10f6cf2010cf5b6ce869ce07f', '--parity', $semanticParity, '--parity-sha256', (Get-FileHash -Algorithm SHA256 -LiteralPath $semanticParity).Hash.ToLowerInvariant(), '--smoke', $semanticSmoke, '--smoke-sha256', (Get-FileHash -Algorithm SHA256 -LiteralPath $semanticSmoke).Hash.ToLowerInvariant())
$semanticNodeMode = $env:ELECTRON_RUN_AS_NODE
try {
    Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
    $semanticStdout = Join-Path $semanticRoot ('operator-audit-' + [guid]::NewGuid().ToString('N') + '.stdout')
    $semanticStderr = $semanticStdout + '.stderr'
    $semanticProfileSwitch = '--user-data-dir=' + $semanticProfile
    $semanticArguments = @($semanticHelper, 'audit', $semanticProfileSwitch) + $semanticLiveInputs
    $semanticProcess = Start-Process -FilePath $semanticExe -ArgumentList $semanticArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $semanticStdout -RedirectStandardError $semanticStderr
    if ($semanticProcess.ExitCode -ne 0) { throw 'SEMANTIC_AUDIT_FAILED_INSPECT_RECEIPT' }
} finally {
    if ($null -eq $semanticNodeMode) { Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue } else { $env:ELECTRON_RUN_AS_NODE = $semanticNodeMode }
}
```

Every example path above contains no spaces; properly quote any
operator-supplied path that does.
Keep normal Electron mode and the exact profile for every live phase below.
The helper verifies the production health identity, candidate bytes, selected
source modules and unchanged production descriptor. A runtime refresh requires
fresh runtime pins. HTTP client reconnect alone proves no runtime refresh.

## Rejection checkpoint and proof-only replan

Use `accept --apply --claim-controller` only when audit proves passed proof on
every original exact wave. When audit shows 20 ACCEPTING waves without proof:

1. Launch mode `reject` with the same live inputs plus
   `--apply --claim-controller`. Retain its final `semantic-reject-*.json` receipt.
2. Display an operator-visible checkpoint stating original action/run/wave
   IDs, preserved postimages, missing original proof, REPLAN status, exact report
   IDs and next action. The supported acknowledgement records this checkpoint;
   it does not record new user approval.
3. Launch mode `replan` with the same live inputs plus
   `--apply --claim-controller --operator-checkpoint-reported --verify-command-approved
   --rejection ABS_FINAL_REJECTION_RECEIPT --rejection-sha256 EXACT_REJECTION_SHA256
   --verifier-sha256 a92245b8502e4693cd67bd748366147bcae00464e91e1758c5b638d49cb1d848`.

The replan verifies the exact persisted rejection latch, acknowledges it using
supported `task_control update`, then executes
`node tests/fixtures/native-first-canary/verify-postimages.cjs` through ordinary
local command execution with a 60-second workflow budget and a 90-second HTTP
bound. If handed a background operation, it observes that original handle.
Acceptance requires exact command hash/stage, exit zero, current source scope,
no cache reuse and a new proof wave in the original RUN. Intent receipts refuse
replay after uncertain mutation. A failure requires original-handle/RUN audit.
