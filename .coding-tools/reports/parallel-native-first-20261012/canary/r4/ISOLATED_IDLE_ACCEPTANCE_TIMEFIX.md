# Isolated idle acceptance for the parallel-r4-timefix candidate

This is an additive operator note for the current packaged candidate. It leaves the dated r4 helper unchanged as historical evidence.

## Current package

- Candidate: `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix\win-unpacked`
- Parity proof: `E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-timefix-parity.json`
- Smoke proof: `E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\parallel-r4-timefix-smoke-full.json`

## Helpers

Use the additive helpers in this directory:

- `sandbox-idle-policy-timefix.cjs` for `prepare`, `isolate`, and `restore`.
- `prepare-reviewed-idle-pins-timefix.py` for fresh two-root idle pins.
- `invoke-isolated-idle-canary-timefix.ps1` for the controlled remote canary and read-only idle observer.

The helpers bind the package proof, policy receipts, and local supervisor projection to the current candidate. They preserve the three AutoCAD `UNKNOWN` action IDs and do not grant native fixture approval for the isolated lane.

## Safety boundary

The helper copies were syntax checked and exercised only with offline tests. No policy install, SSH action, VM operation, or service mutation was performed while preparing this note. Run `prepare` first and review its receipt before any explicit `isolate --apply`; after the original action is settled, use `restore --apply` and verify both workspace scopes.
