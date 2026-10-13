# Authorized r2 to r3 handoff

Root owns every production operation. Source stays frozen after r3 parity.
The exact r2 owner is PID 35428, start token `134362815903498960`, instance
`a233b450199c09cd3118fb4ca2d7068b`, installation
`1f61bc22f8a5b5c999710b319733ce8983f2ab6ab90ee6f7ab447f615b3facbb`.

The r2 epoch `activation-mv587m4p-0c2b59f01b1d25ba52938db8923db9da` is
admission-closed. Central route evidence is stale because isolated Python cannot
import the new policy-store sibling. Other final-census gates passed. Original
activation records and journals remain untouched by these helpers.

## Procedure

Inherit `PYTHONDONTWRITEBYTECODE=1`. Use `ELECTRON_RUN_AS_NODE=1` only when
running the JavaScript helper under the selected candidate executable. Pass
absolute r3 parity and smoke paths with `--parity-proof` and `--smoke-proof`.

1. Run the r2 executable with `packaged-operations.cjs stop --apply`. This checks
   the exact closed epoch, canonical idle state and absence of Sandbox processes.
   A fixed, exclusive `ordinary-r2-stop-intent.json` is written before dispatch.
   An existing intent refuses any second stop attempt. After response loss,
   observe the original exact owner; do not redispatch stop.
2. Run the r2 executable with `stopped-observation`, then within 120 seconds run
   `retire --apply --stopped-observation <receipt>`. Retirement rechecks zero
   active jobs, stopped MCP/native state, exact UI/supervisor/process identity and
   policy fingerprints. Suppress exact UI and retire only that owner.
3. Run `install-launch.ps1 -Operation InstallSupervisor -Apply` with absolute
   `-RetirementReceiptPath`, `-ParityProofPath`, and `-SmokeProofPath`.
4. Run `install-launch.ps1 -Operation LaunchUi -Apply` with the same proofs and
   exact `-InstallReceiptPath`. It unsets node mode only for UI launch.
5. Root observes r3 and proceeds through supported refresh, exact completion and
   per-workspace policies before canaries.

## Immutable old package

The old r2 executable/archive retain their original parity hashes. Its 309
resource files are pinned in `retiring-r2-resource-snapshot.json`, bound to the
old parity/smoke and installed agent hash. Every old census checks that snapshot
before and after. This is retirement evidence and makes no current-source claim.
The new r3 package retains full current-source, resource and adapter proof.

No cache deletion, database restoration, journal editing, generic process kill,
or repeated stop is part of this procedure.

## Canary policy operations

The r3 controller also supports the following modes under the verified r3
executable, with `--apply`, the same absolute parity/smoke proofs, and
`--epoch <exact current READY epoch>`:

- `canary-build --fixture-manifest <absolute Codex fixture manifest>` adds the
  exact reviewed Node build prefix and installs `native_only` on Codex-web.
- `canary-overlap --fixture-manifest <absolute two-root fixture manifest>` adds
  each exact reviewed hold-script prefix and installs `native_only` on both roots.
- `final-policy --baseline-receipt <canary-build baseline receipt>` restores
  `native_first` and both original native prefix lists. It permits removal only
  of the exact two canary additions; other concurrent approval changes block it.

Every mode requires current exact owner identity, READY admission and local idle
Job state. The canary modes write a two-root `canary-policy-baseline` before
mutation and a receipt after each verified target. Use the first build baseline
for final restoration; the overlap baseline already contains the build approval.
Receipts survive partial failures and identify the baseline and completed
targets. Observe current exact policies after an uncertain response before
deciding the next operation. An explicit later READY epoch may restore a baseline
from the same package and workspace generations after a controlled reconnect.
