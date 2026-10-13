# r5 continuation evidence join

This addendum joins only existing, immutable r4 receipts. It does not contact
Ubuntu, redispatch an action, alter policy, or turn a failed parent harness into
a pass. The parent file API canary failed closed at the old native identity
check after recording 100 reads, 20 patches, and 20 readbacks. Its terminal task
and writer were already verified closed/released. The additive continuation
receipts then prove 10 Node jobs and `git_status`; the resume proves `git_diff`,
`git_log`, and the explicitly approved build; the successful finalizer proves
the build artifact readback.

Run from the repository root:

```powershell
$r4 = (Resolve-Path '.coding-tools/reports/parallel-native-first-20261012/canary/r4').Path
$r5 = (Resolve-Path '.coding-tools/reports/parallel-native-first-20261012/canary/r5').Path
$out = Join-Path $r5 'native-first-continuation-evidence-join-20261013.json'
python (Join-Path $r5 'aggregate-native-first-continuation.py') `
  --original (Join-Path $r4 'shared-mcp-receipt-e343984bfcee4e8fb5f9de04038596a7.ndjson') `
  --continuation (Join-Path $r4 'continuation-receipt-0fe3b0d6d1e44d8284760356bea309fc.ndjson') `
  --resume (Join-Path $r4 'continuation-resume-receipt-9509199d0c7b49bba496c971676a4882.ndjson') `
  --readback (Join-Path $r4 'readback-finalizer-receipt-698fcc64e0b5431081e8a4e90fb7569f.ndjson') `
  --output $out
```

The expected status is `lanes_complete_semantic_gate_separate`, with counts of
100 reads, 20 patches, 20 readbacks, 10 Node jobs, 3 Git jobs, 1 approved
build, and 1 build readback. The report deliberately leaves these gates open:
semantic acceptance, the three preserved AutoCAD `UNKNOWN` actions, and a real
`.NET`/AutoCAD build.

Offline tests:

```powershell
python .coding-tools/reports/parallel-native-first-20261012/canary/r5/test-aggregate-native-first-continuation.py
```

## Production checkpoint

`production-final-evidence-20261013-v3.json` joins the continuation report
with the independent 20/20 semantic audit, 2078 ms two-root overlap, corrected
idle observation, both current `native_first` policy receipts, the latest
Ubuntu readiness, and the latest Windows READY status. Its central executor
classification closes the direct connector discovery gate while preserving the
raw `CHANGED_NEEDS_DISCOVERY` diagnostic. It records the Windows census as
`RUNTIME_BUSY` because the runtime-state process is live even though active
commands, managed processes, and sidecar residues are zero.

The checkpoint status is `production_runtime_ready_with_acceptance_gates_preserved`.
The remaining gates are the three quarantined AutoCAD `UNKNOWN` actions, a real
`.NET`/AutoCAD build, and the dedicated idle teardown receipt limitation.
