# Native full-suite reconciliation — 2026-10-11

Observed at 2026-10-11 14:24:28 UTC / 21:24:28 Asia/Saigon.
Repository: `E:\Github\Tools-Codex-web`, dirty `main` at
`2c554f59cb7b8ffc86ce5e0e28076c792777642f`.

## Gate result

The required post-extraction full native suite completed with **1218 passed,
5 failed, 5 skipped** in 523.00 seconds. It is not a green full-suite result.
All 10 approved-patch initial-verification tests passed in that run.

The bundled Python interpreter lacked pytest. After the root controller
authorized the verified system interpreter, the completed full-suite command was:

```powershell
& 'C:\Users\daoth\AppData\Local\Programs\Python\Python311\python.exe' -B -m pytest tests/ -q
```

Working directory: `E:\Github\Tools-Codex-web\resources\coding-tools-mcp`.
No dependencies were installed.

## Failure classification

| Full-suite failure | Cause and strongest follow-up evidence |
| --- | --- |
| `EfficiencyRuntimeTests::test_workspace_context_exposes_non_secret_runtime_activation_identity` | Root delegated this case to the JS review lane. That lane corrected the fixed expected contract hash and reported an exact focused PASS. This native lane did not change the case. |
| `RunContinuationSurfaceTests::test_internal_structured_argv_uses_no_shell_and_is_not_a_public_escape_hatch` | `SANDBOX_HOST_BUSY` in the existing state-aware backend's `_ensure_active` before provision and before command spawn. Live integration remains unvalidated on the shared host. |
| `RunContinuationSurfaceTests::test_patch_proposal_journals_backup_runs_structured_proof_and_stops_at_accepting` | The same fail-closed shared-host preflight boundary, before command spawn. No adapter/extraction regression was demonstrated. |
| `RunContinuationSurfaceTests::test_failed_proof_dispatches_one_bounded_repair_turn_then_reaches_accepting` | The same fail-closed shared-host preflight boundary. Synthetic-boundary proof verifies the failed-check → bounded repair → ACCEPTING state transitions, but does not validate a real VM. |
| `CommandHandleMigrationTests::test_control_plane_structured_argv_requires_attested_bridge_identity` | The test required `exited` from a 1000 ms initial yield. Yield is measured from exec entry; MXC preparation can consume it, making `running` a valid first observation. The test now polls the same original command up to 30 times at 1000 ms, accumulates stdout, and preserves terminal, authority, exit-code, literal-output and junction-warning assertions. Exact real focused retry: **1 passed in 1.98s**. The existing feature=False fixture uses legacy MXC and starts no Sandbox VM. |

The three continuation cases are real-process integration fixtures rather than
backend mocks. Backend selection, host-busy preflight and initial-yield timing
were not changed by the approved-patch adapter. The current failure sites show
environmental admission refusal; a successful live continuation run was not
claimed.

## Isolated boundary proof

Diagnostic `initial-proof-native-isolated-boundary-20261011-r2.py` ran the four
original continuation/Wave A assertion bodies with OS boundaries replaced by
synthetic processes. It leaves source patches, temporary ledgers, workflow
state transitions, provenance and session observations real.

Result: **4 tests passed** in 13.701 seconds; five synthetic command spawns all
asserted `shell=False`; one postimage proof intentionally failed and the bounded
repair reached ACCEPTING. Wave A observed `running` and polled exactly one
original command. No actual subprocess or VM was created by this diagnostic.
This is extraction/state-machine evidence, not live MXC acceptance.

The first diagnostic also passed all four test bodies, but its wrapper exited
1 because a time-based synthetic delay did not force polling through local
ledger overhead. Revision r2 uses a deterministic poll counter and passes the
additional same-command polling assertion. Both original artifacts are retained.

## Edits and evidence

No production source was edited during this reconciliation; the root's r11
source freeze remains intact. Changed test:
`resources/coding-tools-mcp/tests/test_wave_a_runtime.py`.
Its SHA256 is
`189cafa27e75ec0170c2635e7994bb8aa326d61ca9c18ecc0a1a51254dbcaf8a`.

Evidence in this directory:

| Artifact | SHA256 |
| --- | --- |
| `initial-proof-native-full-suite-20261011.log` (bundled pytest unavailable) | `d34b205f9c3e36c7c36edb3edff3e8fd854dfd0929da7fa8041a9cdd42769a3e` |
| `initial-proof-native-full-suite-system-20261011.log` | `53dbfcda2f4f4d552374f56ac99adb6f64102511289edd5922886748161534bc` |
| `initial-proof-native-isolated-boundary-20261011.py` | `8683e0f6a0b648aa87ea0e4e53cb204cddf16e871c22bed5cc51c654bb712ef0` |
| `initial-proof-native-isolated-boundary-20261011.log` | `3577b1920cf29f6b837019de81b4dee5d1e9a328b1e51c626820bb3e4b8d1740` |
| `initial-proof-native-isolated-boundary-20261011-r2.py` | `0e2ade6a475d02b43f6a7731ffd5c0957d2004eca1106fc7c7ae87ff8168b378` |
| `initial-proof-native-isolated-boundary-20261011-r2.log` | `718ea7dd25d6d1ca3f073d5cd4e549838c06f094ed70f0859e5b171d85f3a6ea` |
| `initial-proof-native-wave-a-polling-20261011.log` | `62c7ef6a85ea5c2678432dafb13eba55a1c7638732c5574005a7292cd59fd1fa` |

Scoped `git diff --check` passed for the six native modules, the new initial
verification tests and the changed Wave A test. Git HEAD and branch remain as
observed above. All full-suite, diagnostic and focused-test sessions in this
lane have terminated. No commit, push, rollout, grant, service restart, VM
cleanup, feature modification or Windows reboot occurred in this lane.

## Remaining gate and next action

Do not mark the original full native suite green. The two test-contract/timing
failures have focused passing follow-up evidence; the three live continuation
cases require a controlled Sandbox run while the shared host is available.
The root controller owns that runtime decision. Continue with the root's
packaged-candidate acceptance using this explicit remaining integration gate;
do not automatically destroy or restart shared-host resources.
