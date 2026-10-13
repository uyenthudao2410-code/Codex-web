# r3 to r4 guarded handoff

This directory contains additive helpers only. No runtime call, process stop, policy install, supervisor install, or UI launch was performed while preparing them.

## Inputs

- Old candidate: `dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r3/win-unpacked`
- New candidate: `dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4/win-unpacked`
- r4 parity: `.coding-tools/reports/native-first-20261012/parallel-r4-candidate-parity.json`
- r4 smoke: `.coding-tools/reports/native-first-20261012/parallel-r4-packaged-smoke.json`
- Original r3 native-first baseline: `parallel-r3-transition/canary-policy-baseline-1791809168575-0779bf7e.json` (SHA256 `126534d0440e0497932c96c4dbe6dcc097794c9780e4014f3b7cd0da461a6298`)

Before each mutation, capture a fresh sanitized server readiness report. Pass it as `--server-fence`. The controller requires exact current device and both target registrations, zero current live tasks/writers/queued/active dispatch, the three Autocad quarantined unknown actions, and preserved foreign expired blockers. It does not claim or infer an admission fence.

## Controller sequence

Run the controller under the exact old r3 executable with `PYTHONDONTWRITEBYTECODE=1` and `ELECTRON_RUN_AS_NODE=1`:

1. `stop --apply --parity-proof <r4 parity> --smoke-proof <r4 smoke> --server-fence <fresh report>`.
2. `stopped-observation --parity-proof <r4 parity> --smoke-proof <r4 smoke>` and verify its exact owner/census.
3. `retire --apply --stopped-observation <observation> --parity-proof <r4 parity> --smoke-proof <r4 smoke> --server-fence <fresh report>`.

Preserve failed receipts and one-shot intent files. Never replay an uncertain stop or retirement.

## Install and launch

After a successful retirement, run `install-launch.ps1 -Operation InstallSupervisor -Apply` with absolute retirement, r4 parity, and r4 smoke paths. Then run `LaunchUi -Apply` with the install receipt and the same r4 proofs. These steps require `PYTHONDONTWRITEBYTECODE=1`, check source hashes and smoke cleanup, and never infer readiness from the spawned PID.

After a fresh r4 READY observation, use the controller's `canary-build`, `canary-overlap`, `final-policy`, and `policies` modes. `final-policy` is cross-package and requires the exact original r3 baseline plus the current r4 parity.
