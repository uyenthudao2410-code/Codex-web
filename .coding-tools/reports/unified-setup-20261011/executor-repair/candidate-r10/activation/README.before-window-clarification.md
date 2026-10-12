# Guarded r9 → r10 operational packet

Prepared on 2026-10-11. This directory does not deploy Ubuntu or mutate authority. The helper exposes read phases and explicitly guarded local mutation phases. No mutation phase has been executed while preparing this packet.

## Frozen targets

- Repository: `E:\Github\Tools-Codex-web`, `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`; existing dirty work preserved.
- Local profile: `C:\Users\daoth\AppData\Roaming\web-mcp-assistant` on DaoChienThang.
- Old candidate: `executor-lifecycle-1011-r9`; old epoch `activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7`.
- New candidate: `setup-exec-contract-1011-r10` under `dist/windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked`.
- New archive SHA256: `c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9`.
- New executable SHA256: `6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f`.
- Parity receipt SHA256: `c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c` (11 changed source files, 4 unchanged native resources, 7 unchanged UI inputs; only 136 verified cache removals beyond the 11 code deltas).
- Ubuntu target: `svhome@100.116.112.22`, user service `codex-control-plane.service`.
- Required Store revision: `395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5`; package source SHA256 `sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419`.
- Required authority helper: `executor-repair/store-delta/ubuntu-r10-store-authority-v2-pinned.py`, SHA256 `ab182f47b605e5edac1e30cb9cdf48ca53a571f0cbb5367a0f6fb837cbe0c9af`.
- Binding: `bind_3e05bf64cb3e4bab93d930ae1692bebb`; workspace `workspace_dda1d78e9a21402aa6213f72af64f788`; generation `generation_c2f13e8d02344cf6a38a3f42ecfa59b6`; device `72ceec2d-e3f2-472f-8e3c-99fffe053035`.

## Read-only proof completed

`freeze` and `preflight` completed at 19:17:17 and 19:17:38 +07. The exact r9 identities matched the previous final census:

| Component | PID | Process start token |
| --- | ---: | --- |
| Recovery Host | 1128 | 134361911908524600 |
| UI | 25296 | 134361911886531150 |
| Native MCP | 9212 | 134361911931895600 |
| Connected agent | 7108 | 134361912150770020 |

Installation `e65d60602938af2f1c6e8cd9e8c59352ff2a5e24a268a45a98114726cdd8210d`, instance `6006092b7a061f47b20a0b27c1f34f1d`, UI instance `2d80b88288e54bcc40f86f6ad45adcf6` and the old epoch matched. The native/UI/Host remained live, the managed tunnel was absent, and the epoch was READY.

The canonical census had zero active commands, starting commands, tool calls, background operations, managed jobs, heavy processes and agent lanes. Its only expected `RUNTIME_BUSY` blocker was `live_runtime_state_process`; ledger integrity was `ok`, with no ledger mutation. Pending run `95e909f0040a448faa9f1f3257e2ee2c` and wave `c101beadfc6d4f2fbc13845052c84693` retained their exact record hashes.

Independent observations used fixed trusted System32 PowerShell commands: `Get-Process` for Windows Sandbox/vmmem host processes and CIM for the MXC daemon/exec/guest host processes. Both counts were zero at both read checkpoints. These observations do not start a VM, run a test, reclaim a VM or prove executor acceptance.

`r9-identity-pin.json` SHA256: `c82a566d793278e0e831e20e8153fa48dbdb8d04db7fe3e1162c8245bbbab24b`. All observations are retained in `windows-activation.jsonl`.

## Required approval and server evidence

The root controller must review this helper, then obtain new explicit user approval for the grouped operation: deploy the frozen Store packet to `svhome@100.116.112.22`, restart `codex-control-plane.service`, close/reopen intake, activate r10 on `web-mcp-assistant`, and renew Read/Edit/Exec for exactly this repository for 60 minutes. Windows reboot and VM/HCS termination are excluded. Earlier r9 approval is insufficient.

After approval, the root creates `authorization.json` from the example and records the actual user approval evidence. The example has `approval_received: false` and cannot authorize anything. The local helper requires the exact local action list, candidate hashes, profile, target and parity. Server deployment is performed separately by the root using the approved Store packet; its target and revision can additionally be recorded in `server_operations`.

After Store deployment leaves intake in recovery, use the pinned v2 Store helper to observe, close and renew against the fresh old r9 epoch and heartbeat. Save its exact JSON output, without editing fields, under these local names:

1. `server-preflight.json`: `r10_store_read_only_preflight`, recovery mode, exact new Store package/source and service instance, fresh r9 predecessor epoch/heartbeat, protected state hash.
2. `server-intake-closed.json`: `intake_closed`, recovery, same service/source and state.
3. `server-authority-renewal.json`: `same_scope_renewal_complete`, recovery, same service/source/state, exact context/pilot and workspace policy assignment, deadline exactly requested time + 3,600,000 ms.

The mutation receipts intentionally omit the package hash; the mandatory independently pinned preflight proves that package hash. Both receipts must match its service instance and complete protected state SHA256. Original 13 quarantined actions, acceptance digest and all protected action/task/intent families must remain unchanged. Intake closure and preflight must be less than 10 minutes old; renewal must remain unexpired. No old expired policy receipt is accepted.

## Commands after root review and approval

Run from the repository root in PowerShell. `freeze` has already saved an immutable pin; running it again with the same fixed pin filename refuses overwrite. `preflight`, `census` and `status` may be repeated when live state changes.

```powershell
$r10ActivationScript = '.coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/activation/activate-r10.cjs'
node $r10ActivationScript preflight
```

After the four approved evidence files exist, compute their hashes and use those exact values for each mutation phase:

```powershell
$r10EvidenceDirectory = '.coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/activation'
$r10MutationArguments = @(
  '--operator-approved'
  ('--authorization-sha256=' + (Get-FileHash -Algorithm SHA256 -LiteralPath "$r10EvidenceDirectory/authorization.json").Hash.ToLowerInvariant())
  ('--server-preflight-sha256=' + (Get-FileHash -Algorithm SHA256 -LiteralPath "$r10EvidenceDirectory/server-preflight.json").Hash.ToLowerInvariant())
  ('--closure-sha256=' + (Get-FileHash -Algorithm SHA256 -LiteralPath "$r10EvidenceDirectory/server-intake-closed.json").Hash.ToLowerInvariant())
  ('--renewal-sha256=' + (Get-FileHash -Algorithm SHA256 -LiteralPath "$r10EvidenceDirectory/server-authority-renewal.json").Hash.ToLowerInvariant())
)
node $r10ActivationScript activate @r10MutationArguments
```

`activate` rereads the frozen package/source proofs and exact runtime identities, then requires a quiescent census and two independent fresh zero VM observations immediately before each retirement boundary. It retires only the pinned connected agent, sends the exact old UI stop signal, stops the exact owned old native runtime, retires the pinned Recovery Host without descendants, and launches the pinned r10 executable. The old r9 native service lacks the new executor cleanup endpoint, so a nonzero or unavailable host/daemon observation refuses the transition. There is no VM/HCS kill or automatic retry/fallback. If a boundary fails after a partial retirement, retain the JSONL evidence and review the observed state before taking another action.

Optional metadata assignment synchronization uses the existing enrollment route, then verifies the existing standing file/patch/exec policy hashes and exec allowlist are unchanged. It does not install standing policies or perform a standalone Sandbox probe:

```powershell
node $r10ActivationScript policy @r10MutationArguments
node $r10ActivationScript refresh @r10MutationArguments
node $r10ActivationScript agent @r10MutationArguments
```

Use `refresh` only when required to complete the new epoch after policy synchronization. It keeps pending semantic acceptance and does not run code or accept a task. `agent` starts the same bounded connected trial as r9: 200 iterations, 15-second interval, 60-second maximum backoff. It refuses an old live agent and reuses its already recorded exact new agent identity if invoked again.

The server controller then observes the fresh r10 epoch and uses the v2 Store helper to reopen scoped pilot only against that distinct epoch, a fresh heartbeat and enabled policy. The original local renewal receipt is retained unchanged. Finally:

```powershell
node $r10ActivationScript proof @r10MutationArguments
```

`proof` is read-only. It checks exact r10 descriptor/Host/UI/native/agent identities, READY epoch and fresh heartbeat, unchanged source/package/standing policies, quiescent canonical census and unchanged pending run/wave records. It does not claim a live Sandbox test or product acceptance. Any subsequent live canary must have separate fresh action identities and must not replay old attempts.

## Stop conditions

- Missing new approval, changed proof/source/package, unexpected process identity, active Job/lane, altered pending acceptance record or altered server quarantine family: refuse.
- Any Windows Sandbox/vmmem/MXC process, unavailable independent observation or unsafe census: keep the observed runtime and refuse the next retirement step.
- Expired renewal or stale closure/preflight: renew/observe using the approved same scope; do not extend timestamps by editing evidence.
- Root alone controls Ubuntu deployment/restart/intake and authority. This helper cannot perform those operations.

No commit, push, public release, Windows reboot, pending-run acceptance, command replay or VM termination occurred while preparing this packet.
