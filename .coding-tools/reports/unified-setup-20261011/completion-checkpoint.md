# Unified setup and code execution — preparation checkpoint

Date: 11 October 2026, Asia/Saigon. Repository: `E:/Github/Tools-Codex-web`.
Observed HEAD: `2c554f59cb7b8ffc86ce5e0e28076c792777642f`, dirty `main`.

## Completed

- `electron/main.js`: one trusted primary native window for setup, execution,
  task results and current machine; no second manager or task overlay.
- `renderer/index.html`, `renderer/settings-compact.css`, `renderer/app.js`:
  connection, folder permissions and execution checks share one System page.
  Local consent binds server/device/workspace/generation/capabilities; bounded
  15-second observations wait at most ten minutes, then synchronize existing
  metadata, file and exec policy APIs. Scope changes/cancellation fence later
  calls. Receipt mismatch, partial file policy and missing Sandbox block exec.
  Resuming restores opaque selection only; full exit loses local consent.
- `control-plane/control_plane/web_ui.py`: one owner folder form selecting
  machine/folder/duration, using existing authenticated binding/context calls.
  Manual controls remain in Advanced; pilot/grant/admission remain explicit.
- Focused tests and current guidance updated in `docs/CURRENT_STATE.md`,
  `docs/MCP_WEB_OPERATIONS.md` and `docs/TESTING.md`.

## Proof and artifacts

- Six Node suites: 106 distinct successful cases. `final-focused-tests.log`
  has 105 successful cases; after one additional main-action test,
  `setup-final-tests.log` has 17 successful setup cases. Remaining five suites
  reuse proof from the same unchanged source. No skipped tests in those receipts.
- `test_web_ui_folder_setup.py`: eight successful behavioral cases; prior
  focused service/CSRF checks were also successful on unchanged server source.
- Adjacent toolbar regressions initially failed because their fixtures assumed
  a second manager window; fixtures now enforce one window and all ten pass.
  Earlier lifecycle receipt's three failures are superseded by that proof.
- Candidate: `dist/windows-candidate-mxc-wsb-cbe1774-unified-setup-1011-r7/win-unpacked`.
  Build succeeded; `windows-smoke-r7.log` proves isolated Recovery/MCP startup,
  fail-closed checks, separate test profile and unchanged production descriptor.
  `windows-candidate.json` proves eight exact Electron/renderer source matches
  and normalized packaged package identity. `candidate-delta.json` proves only
  four UI code files differ from r5; packaged resource code has no delta.
- `static-layout-checkpoint.md` / preview08: 22 static captures, three widths,
  light/dark, pending/blocked/verified policy scenarios; no horizontal overflow.
  Synthetic snapshots are layout proof only.
- `server-review/receipt.json` and README bind frozen `web_ui.py` delta
  `03e5279c89bf4b1c04ef0139724e77eb960a3efdca32aa59ec2445e3b35fc64b`
  to the prior `beaa9d5a` archive. Both review/exact patch replays and syntax
  checks passed. This is a one-file delta, not a newly deployed server release.
- Scoped syntax/whitespace/conflict review passed; index remains unchanged.

## Runtime, authority and remaining work

No new shared Windows activation, SSH operation, Ubuntu deployment/restart,
authority renewal, primary commit/push, tag or public release occurred in this
wave. Isolated candidate smoke and static previews have exited.

Read-only `local-job-census.json` reports no managed jobs, no unexplained active
runs and no unbound live resource residues. One prior acceptance boundary
remains recorded: RUN `95e909f0040a448faa9f1f3257e2ee2c`, WAVE
`c101beadfc6d4f2fbc13845052c84693`. It has not been accepted or rewritten.

Last verified live installations remain Windows r5 on `web-mcp-assistant` and
Ubuntu revision `beaa9d5a` on `svhome@100.116.112.22`. Their prior scoped
authority expired at 16:26:24.008 +07; this wave does not renew it.

Remaining live gate: operator approval naming r7/profile activation, the prepared
Console delta/server service operation and a fresh 60-minute authority window
for the exact Tools-Codex-web binding is needed before live execution checks.
After approval, reverify live baseline and inflight work, build a versioned
server artifact from the frozen delta, preserve rollback, roll out the named
targets and test continuation plus a harmless focused test through Ubuntu MCP.
Already sent operations must be reconciled rather than silently retried.

Material limitation: the current owner binding/context APIs are non-atomic
across independent Console tabs. The form prevents its own retries/duplicate
live contexts, but concurrent owners can still require Advanced reconciliation.
