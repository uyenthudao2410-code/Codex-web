# r10 source and package checkpoint — rollout pending

Repository: `E:\Github\Tools-Codex-web`, dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`.
Observation date: 2026-10-11, Asia/Saigon. Existing edits and historical evidence are preserved.

## Product changes prepared

1. URL-safe native command, Job and consumer IDs may start with `-` or `_`.
   The affected validators now agree with the actual native generator. Action,
   workspace, task and authority IDs keep their separate strict contracts;
   policy, output hash and exact correlation checks are retained.
2. Standing setup no longer depends on unconditional compact metadata assignment
   or that assignment's TTL. Existing exact-target authenticated authority,
   standing installers, fresh observations and owner consent still apply.
3. Native full-clean prepare closes the exact owned Sandbox manager asynchronously.
   A fixed cleanup deadline and independent admission barrier survive prepare
   fence expiry. Completion needs literal confirmation and the same manager.
   Electron observes that one attempt with the same operation/process/server
   identity, renews only the short fence, and preserves the native owner if
   cleanup or the response cannot be confirmed. Legacy live runtimes lacking
   the cleanup marker are refused before epoch/process mutation.
4. Ubuntu Store assignment excludes only the six internal operation contexts
   having complete owner/binding/action/request/context joins. Generic owner
   metadata contexts remain eligible and real ambiguity remains an error.
   This is in a separate immutable server packet, not part of Windows activation.

## Frozen Windows package

- Candidate: `dist/windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked`.
- Source freeze: `source-freeze-20261011T115648871Z.json`, SHA256
  `030893e3e3f056debb1ee8b4213e4b4c1ae0fdb28af63ba8313567a3e231049f`.
- Parity: `candidate-parity-20261011T115907669Z.json`, SHA256
  `c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c`.
- app.asar SHA256: `c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9`.
- Executable SHA256: `6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f`.
- 11 changed source paths match their payload; 4 critical/native resource paths
  and 7 UI files are unchanged from r9. 136 removals are verified Python caches
  whose corresponding source is checked. No cache additions, unexpected payload
  differences, missing expected delta or source drift was accepted.

The exact 11 changed paths are renderer/app.js; electron/services/runtimeOrchestrator.js,
recoveryIpc.js, controlPlaneExecBridge.js and fullCleanActivation.js;
control-plane/control_plane/node_agent.py and recovery_exec_bridge.cjs;
resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py, exec_tools.py,
mcp_http_handler.py and windows_mxc_state_aware.py. Native MXC binaries remain
unchanged. This is an unpacked development candidate, not a signed public release.

## Proof receipts

| Boundary | Receipt | Result |
| --- | --- | --- |
| Native ID adapters | Worker frozen focused receipts | 55 PASS |
| Standing setup/policy | Worker frozen focused receipts | 57 PASS |
| Store assignment/HTTP ambiguity | Worker frozen focused receipts | 7 PASS |
| Native cleanup/preflight/state-aware/spawn | ../graceful-executor-cleanup/SOURCE-PROOF.md | 72 PASS |
| Full-clean and new cleanup protocol cases | full-clean-cleanup.log | 75 PASS |
| Recovery/runtime suites | recovery-runtime.log | 138 PASS; one stale UI source assertion failed |
| Corrected UI readiness assertion | targeted-ui-proof-final.log | 1 PASS |
| Real isolated Recovery process boundary | recovery-process.log | 3 PASS |
| Candidate build | windows-build-r10.log | exit 0 |
| Isolated packaged Recovery smoke | windows-smoke-r10.log | PASS; production descriptor stable |

Receipts have overlapping coverage; the rows are not an independent aggregate
test count. Initial failed assertions remain evidence. The stale UI assertion
expected a separate manager window and `chatWindow.loadFile`; the current unified
window uses guarded `openingWindow.loadFile` and manager navigation reuses it.
The focused correction retains visibility-before-registration checks. No
production UI code was changed merely to satisfy that stale assertion.

## Live boundary and next action

r9 remains serving the exact profile; a 4-PASS cold MCP canary is verified.
The distinct warm native exit-0 attempt had a rejected relay envelope and was
evidence-bound reconciled failed/settled without replay. At 18:49:11 +07 the
live census had no open trial task/writer or active command/lane; the historical
13 quarantine families and pending local RUN/WAVE acceptance hashes are unchanged.
Ubuntu is still on `5ce5c51f…`, service `cp_d203277517b747e4b056ec0184d09709`.
Authority remains exact folder, ending 19:19:16.518 +07.

Two fresh read-only observations at 19:16:26 and 19:16:58 +07 found zero Sandbox
host processes and no daemon record, without opening the record. Both exact
runtime/server censuses passed; no new timeout canary was executed. Guarded
r10 freeze/preflight passed at 19:17:17–19:17:38 with zero VM/backend observations.
The cleanup cause is unknown; this is absence evidence, not legacy cleanup API
confirmation. Re-observation is mandatory immediately before each effect.

Owner read-only server receipt at 19:20:40 +07 is retained in
`server-before-approval-20261011T122040809Z.json`, SHA256
`e701e8b69bd3bce302fab463232b3103917a94ae05ee3383d568ba18a7ecaed5`.
Source/service and action/task/acceptance state remain unchanged. The old trial
window has expired; the grouped r10/Store/new 60-minute approval is pending.
No post-expiry test or authority renewal has been performed.

Next: obtain AGENTS.md §5 approval for the frozen r10/profile and Store snapshot
`395c7868…`/Ubuntu service operations and the exact new trial window, then perform
guarded activation and live cold/warm/timeout/setup verification. A legacy Job
terminal flag is not VM teardown proof. Ordinary stops bypassing prepare, controller proof/acceptance,
durable delegation/agent lifecycle, actual ChatGPT workflow and signed/reproducible
installation remain explicit gates. No semantic acceptance is manufactured.

No commit, push, tag, release, new Windows activation, Ubuntu deployment/restart
or Windows reboot was performed while preparing this packet. Build/smoke/test
sessions have finished; later controlled live experiments must record their own
state and terminal evidence.
