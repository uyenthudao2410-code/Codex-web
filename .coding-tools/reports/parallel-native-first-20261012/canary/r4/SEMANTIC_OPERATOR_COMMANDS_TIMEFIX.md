# Timeoutfix semantic acceptance operator commands

This is an additive reviewed copy of `local-semantic-acceptance.cjs`.  The
original failed canary remains immutable and is supplied as `--canary`; the
fresh `native_exec_continuation` receipt is supplied as `--continuation`.  The
helper requires the exact failed error (`ORIGINAL_JOB_IDENTITY_NOT_VERIFIED`),
100 reads, 20 patches, 20 readbacks, terminal node_01, task closure and writer
release, plus 10 new Node jobs, 3 Git jobs, the approved build and readback.
It binds the continuation to the SHA-256 and task identity of the failed
receipt, and never replays an original action.

Reviewed helper SHA-256:
`c8292505250e6568ce8e79837ff37d1369cf332d6dcbc3356dbc90c459613b87`.

Set these paths to the actual immutable receipts after continuation completes:

```powershell
$r4 = 'E:\DEV\Codex-web\.coding-tools\reports\parallel-native-first-20261012\canary\r4'
$partial = Join-Path $r4 'shared-mcp-receipt-e343984bfcee4e8fb5f9de04038596a7.ndjson'
$continuation = 'ABSOLUTE_CONTINUATION_RECEIPT_NDJSON'
$pins = Join-Path $r4 'codex-ready-pins-timefix.json'
$parity = 'E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-timefix-parity.json'
$smoke = 'E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-timefix-smoke-full.json'
$helper = Join-Path $r4 'local-semantic-acceptance-timefix.cjs'
$helperSha = 'c8292505250e6568ce8e79837ff37d1369cf332d6dcbc3356dbc90c459613b87'
$partialSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $partial).Hash.ToLowerInvariant()
$continuationSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $continuation).Hash.ToLowerInvariant()
$common = @('--helper-sha256', $helperSha, '--pins', $pins,
  '--pins-sha256', (Get-FileHash -Algorithm SHA256 -LiteralPath $pins).Hash.ToLowerInvariant(),
  '--canary', $partial, '--canary-sha256', $partialSha,
  '--continuation', $continuation, '--continuation-sha256', $continuationSha)
```

Run offline preparation first:

```powershell
node $helper prepare @common
node $helper prepare-verifier @common --prepare-fixture `
  --verifier-sha256 a92245b8502e4693cd67bd748366147bcae00464e91e1758c5b638d49cb1d848
```

For live audit/acceptance use normal stock Electron and a new isolated
operator profile.  Include `--parity`, `--smoke`, their exact current hashes,
and `--operator-exe-sha256 8593db40c0c6e5e3c4b6b0a225b1dc9a549ecdf10f6cf2010cf5b6ce869ce07f`
as described in `SEMANTIC_OPERATOR_COMMANDS.md`.  Replace the helper path and
append `@common` to each `audit`, `reject`, `accept`, or `replan` invocation.
Use `accept --apply --claim-controller` only after audit shows every original
wave has an independently passed proof.  If proof is absent, follow the
documented reject → visible checkpoint → proof-only replan sequence; never
reapply a patch or replay a continuation lane.
