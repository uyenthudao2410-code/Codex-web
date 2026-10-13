# Native exec continuation resume

The first continuation receipt `continuation-receipt-0fe3b0d6d1e44d8284760356bea309fc.ndjson`
is immutable. It proves 10 Node jobs and `git_status`, then fails closed on
the old empty-stderr harness check for `git_diff`; its task and writer are
closed. The resume helper never reuses those action IDs or dispatches Node or
`git_status` again. It opens one fresh task for `git_diff`, `git_log`, the
explicitly approved build and build artifact readback.

```powershell
$r4 = 'E:\DEV\Codex-web\.coding-tools\reports\parallel-native-first-20261012\canary\r4'
$prior = Join-Path $r4 'continuation-receipt-0fe3b0d6d1e44d8284760356bea309fc.ndjson'
$priorSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $prior).Hash.ToLowerInvariant()
& (Join-Path $r4 'invoke-native-exec-continuation-resume.ps1') `
  -ExecuteConfirmedResume `
  -ReadyPinsPath (Join-Path $r4 'codex-ready-pins-timefix.json') `
  -PriorReceiptPath $prior -PriorReceiptSha256 $priorSha -AttemptId (New-Guid)
```

The exec bridge contract treats `stdout` and `stderr` as separate bounded
streams. For the two Git commands the resume records bounded stderr alongside
exit zero, terminal status, no timeout and no truncation; it does not discard
or reinterpret that stream. Preserve both the failed prior receipt and the
resume receipt for semantic evidence.
