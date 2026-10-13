# Authorized r1 to r2 handoff

The r1 refresh failed at package proof before mutation. Its exact Recovery Host is
PID 12420, start token `134362806788971030`, instance
`19cabc607c0b5e63dc5b76a1a0840a45`, installation
`3fbc272f6eafdf6c61be5458714d6929d8d849c8584f72337aa72a31a190fd6b`.

Root coordinates every production operation. This helper does not support a stop
operation. It retires only that exact stopped r1 owner after a fresh canonical
census and linked stopped observation. Historical evidence is preserved.

## Preconditions

- New candidate: `dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r2/win-unpacked`.
- New proof: `parallel-r2-candidate-parity.json` and `parallel-r2-packaged-smoke.json` in the parent report directory.
- Old r1 executable and app archive must match `parallel-r1-candidate-parity.json`.
- Inherit `PYTHONDONTWRITEBYTECODE=1` for each helper, supervisor install, and UI launch invocation.
- For the JavaScript helper, run the selected candidate executable with `ELECTRON_RUN_AS_NODE=1`.
- The root-owned cache quarantine retains the exact generated r1 cache files and hashes. No cache deletion is required by this helper.

## Operations

1. Run the r1 executable with `packaged-operations.cjs stopped-observation`, passing absolute `--parity-proof` and `--smoke-proof` paths for r2. Both exact source resource gates run before and after census.
2. Within 120 seconds, run that same r1 executable with `retire --apply --stopped-observation <fresh receipt>` and the same r2 proof arguments. It rechecks census, exact process identity, policies, supervisor manifest and UI identity before suppression and retirement.
3. Run `install-launch.ps1 -Operation InstallSupervisor -Apply`, passing absolute `-RetirementReceiptPath`, `-ParityProofPath`, and `-SmokeProofPath`.
4. Run `install-launch.ps1 -Operation LaunchUi -Apply`, adding `-InstallReceiptPath` for the exact installation receipt. The launcher removes the Electron node-mode flag only for the UI spawn.
5. Run the r2 executable with `status`; then supported `refresh --apply`, exact epoch `complete --apply --epoch <id>`, and `policies --apply` as coordinated by root. Every call retains the source/package gates.

Source, offline tests, package parity, isolated smoke and production acceptance
are separate claims. Pending checks remain root-owned: simultaneous native work,
same-Job reconnect, exact workspace/lease preservation, and final idle census.
