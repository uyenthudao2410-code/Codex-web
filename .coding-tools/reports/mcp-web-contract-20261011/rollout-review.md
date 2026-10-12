# Prepared rollout for owner review

Both artifact preparation jobs are complete. This is an explicit request boundary, not a deployment receipt.

## Named targets and artifacts

- Ubuntu: SSH `svhome@100.116.112.22`, owner user service `codex-control-plane.service`, Console `https://svhome.tail0e4032.ts.net/`.
- Current Ubuntu release: `70de202d93c9a759befe5d38491ce54e9ef4b3cd`.
- Prepared Ubuntu revision: `beaa9d5ade4926ef231e3ec9d0a517fe93830e90`; archive `codex-control-plane-beaa9d5ade4926ef231e3ec9d0a517fe93830e90.tar.gz`, SHA-256 `e31132a545da55cad564a373c138bb644917c8cbce73e87b724c88dfee6f3b36`.
- Windows: DaoChienThang, profile `%APPDATA%/web-mcp-assistant`, workspace `E:/Github/Tools-Codex-web`.
- Prepared Windows candidate: `dist/windows-candidate-mxc-wsb-cbe1774-mcp-feedback-1011-r4/win-unpacked`; running r3 is preserved until controlled activation.
- Exact binding: `bind_3e05bf64cb3e4bab93d930ae1692bebb`. Previously authorized Read/Write/Exec scope expired at 15:11:19 +07 on 2026-10-11. Renewal requires the owner's explicit duration and same scope.

## Operations awaiting approval

1. Verify live service/release identity and save recoverable prior release/configuration state without exposing credentials. Transfer the exact candidate, verify its digest/manifest with the unchanged verifier, switch the release and restart the named user service. If verification or health fails, retain/recover the verified previous release through the authorized deployment path.
2. Renew only the same workspace/binding Read/Write/Exec context, local policy and scoped pilot for 60 minutes if approved. The exec capability still requires a separately successful local sandbox probe and valid command policy; renewal does not prove exec readiness.
3. Activate the named Windows candidate using the existing supervised lifecycle and preserve the pending acceptance queue through the supported explicit preservation path. Observe exact replacement identities and loaded source parity, then start/check the scoped connected agent through its supported path.
4. Verify discovery/inventory exposes the facade pin and relay capabilities; reproduce the malformed pin as a model-visible tool error, verify one permitted fixture read, and verify terminal rejection diagnostics. Do not create new writes merely to reproduce already reconciled actions.

Windows reboot is not part of this rollout. Windows Sandbox was enabled but requires an owner reboot; afterward sandbox readiness, exec policy and a permitted harmless command must be proven before declaring live exec ready. An unresolved `WINDOWS_WORKSPACE_REALPATH_EPERM` probe must be diagnosed rather than assumed repaired by reboot.

## Preserved open work

The existing local RUN/WAVE remains acceptance-pending; no fake proof, lease override or ledger edit closes it. Central owner acceptance is a separate fact. Historical UNKNOWN actions remain quarantined/preserved. Directory listing and the central-to-local semantic acceptance adapter remain separate source work, not capabilities added by this candidate.

No push, public release, remote authority change, service restart, Windows reboot or activation occurred during preparation. Source/behavioral proof, build/smoke proof and final local observations are in `validation-checkpoint.md`, `artifact-receipt.json`, `windows-candidate.json` and `final-local-state.json`.
