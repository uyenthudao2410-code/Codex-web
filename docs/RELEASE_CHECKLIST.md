# Release Readiness Checklist — Desktop Execution Hub

This checklist is for the current Windows Electron **Tools-Codex-web / Coding Tools MCP** product. WebCodex core/server/npm release procedures are component-specific.

Do not create tags, push commits, publish artifacts, deploy, rotate credentials, or restart external systems unless explicitly requested.

## 1. Repository preflight

- Verify exact root, branch and HEAD.
- Inspect `git status`; preserve unrelated dirty work.
- Review [`CURRENT_STATE.md`](CURRENT_STATE.md) and `AGENTS.md`.
- Confirm no conflict markers, unintended generated files or secrets are in scope.
- Documentation-only changes normally need scoped `git diff --check` and document/link consistency, not broad code suites.

## 2. Current product contract

Confirm `package.json` version and the verified `smart-v3` eight-tool surface: `workspace_context`, `agent_workflow`, `task_control`, `document_workflow`, `exec_command`, `command_control`, `request_permissions`, `view_image`. `restart_runtime` remains a confirmed `task_control` action. Contract-fingerprint/stale-connector detection must remain intact.

Unless a separately accepted policy change says otherwise, `execution_route=auto` remains deterministic/evidence-gated, high-cost routes require acknowledgement, and provider availability does not silently expand write authority. Public schema changes require a connector-refresh/live-contract plan.

Codex-web has one product version across the Electron package and Python MCP
component. For the current 1.0.7 release, root `package.json`,
`resources/coding-tools-mcp/pyproject.toml`, `coding_tools_mcp.__version__`, and
product-facing version labels must agree on `1.0.7`. Protocol, schema,
tool-contract, ledger-format, and other compatibility identities remain
independent and must not be rewritten to the product version.

## 3. Focused source validation

Use the smallest relevant lane:

```powershell
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run test:recovery:packaged
node scripts/installed-recovery-smoke.js
npm run canary:opencode-flash:preflight
```

The maintained Control Plane focused entry points are the files currently
present in `control-plane/tests`; run them from that package directory so its
imports resolve consistently on Windows and Ubuntu:

```powershell
Push-Location control-plane
python -B -m unittest discover -s tests -p 'test_node_agent_authority_status.py' -q
python -B -m unittest discover -s tests -p 'test_mcp_oauth.py' -q
Pop-Location
```

The historical `test_connected_agent_status.py` example is no longer a
current test entry point. Use `test_node_agent_authority_status.py` for the
authority-status coverage and `test_mcp_oauth.py` for OAuth configuration and
credential-policy coverage.

`npm run canary:opencode-flash` performs real provider dispatch and may incur external cost; run only with explicit authorization. Rust/LSP changes use the smallest affected Rust tests required by `AGENTS.md`.

`npm run dist` currently runs `icon:build`, then `test:all` (both `npm test`
and `npm run test:mcp`), then `clean-dist` before Electron Builder creates the
NSIS candidate. It is therefore a release-boundary test lane, not a substitute
for focused proof while implementing. `npm run dist:dir` builds the unpacked
directory after `icon:build`/`clean-dist` but does not run either test suite.
An installer build alone still does not prove installation, activation, or any
behavior outside the tests it actually ran.

## 4. EOCL and proof integrity

- A green test is not final acceptance by itself; an `ACCEPTING` wave still needs authorized accept/reject.
- Do not accept proof from an older source/worktree fingerprint.
- Check active commands, background operations, provider/agent lanes and write lease before lifecycle operations.
- Preserve canonical evidence in `.coding-tools/orchestration/ledger.sqlite3`; do not manually edit evidence to make a release look clean.

## 5. Controlled activation boundary

Runtime-affecting source tests do not prove the current process loaded new code. Use supported controlled activation and verify expected reconnect, new process/server instance identity, unchanged workspace identity, intended revision/contract, and preserved fail-closed authority state. Do not substitute `taskkill` of the serving MCP for supervised restart.

Before opening a Control Plane scoped pilot after a server update, compare the
live facade contract from the intended principal's `tools/list` and inventory
with every installed standing read/edit/exec policy used by that route. Compare
the exact profile, schema version and SHA; the native smart-v3 fingerprint is a
separate identity. Synchronizing the metadata context alone does not update
standing policy contracts. If they differ, reinstall the policies through the
supported enrollment flow under the existing explicit scope, then verify their
target, path/argv limits, authority mode and validity before dispatch. Do not
disable contract comparison. A rejected action is observed and closed; any new
trial uses separate durable intents and fresh evidence after the cause is fixed.

Explicit central-executor role migration is an operator installation change,
not accepted-code activation. Its fixed `full_clean_execution_role_handoff`
request carries no source/revision/acceptance override and must still pass the
canonical ledger census, exact process stop/fence, durable epoch and local
identity checks. The role can be central while pairing/policy remains pending;
do not call this READY or invent a Windows Tunnel. Central READY requires fresh
independent authenticated route/local policy evidence and the complete central
component census. Verify an expired migration can be explicitly retried and
ordinary Recovery supervision does not restart legacy Windows Tunnels.

Operator `restart` and accepted code/revision activation use the durable
`full_clean_activation` path. It creates a new `activation_epoch_id`, closes
admission, checkpoints durable state, stops Electron UI/Coding MCP/Tunnel and
the configured Recovery MCP/Tunnel, hands off to a replacement Recovery Host,
then requires a final census with matching epoch, workspace, device, revisions,
fresh process identities, real Tunnel health, UI/Recovery Plane health, and a
current-process connector freshness acknowledged through either strict discovery
or the supported exact no-workspace compatibility bootstrap before
`fullyReady=true` can return. Record the actual freshness mode; compatibility
activation does not prove strict rediscovery. Automatic
fault recovery remains `soft_recovery`; it must refuse any newer disk revision
under an older epoch and may not be used as code-update proof.

If the previous activation failed after Coding MCP stopped, verify that an
explicit retry first records a fresh independent Backup-API/query-only ledger
census, rejects active mutation/managed-process or dangerous acceptance state,
and compares a second census while the application ledger gate remains
exclusive through durable epoch creation. A changed ledger hash,
workspace/source checkpoint, or runtime-state PID must fail closed without
stopping a new component set.

For development Electron changes, exercise the deterministic lifecycle with mocked tests first, then—only when local service operation is authorized—use `npm start` or `npm run dev` for the same stable start/focus lifecycle, `npm run dev:replace` for UI replacement, and `npm run dev:refresh` for full-system refresh. A refresh must record the exact development installation, old/new Recovery Host and UI instances, new Coding MCP/Tunnel process identities, one shared `activation_epoch_id`, PID ownership, runtime mode, and `running_revision == disk_revision`; it must never delete durable ledger/configuration/identity state. A stale code activation must still carry the exact checkpoint/run/wave/proof/accepted-HEAD identity from an eligible `auto_activation.closure_input`; capture the typed refusal if that durable authority is absent, incomplete, invalid, or does not own the component. Current-process connector freshness/ACK is a separate gate, so do not call a refresh `fullyReady` while it is `UPDATE_INCOMPLETE`. Use `npm run dev:stop` for a graceful UI-only stop; require an observable exact Recovery Host at entry and either its `MISSING` UI receipt or proof that the prior exact PID exited. Confirm Recovery Host/MCP/Tunnel preservation and watchdog suppression rather than killing `electron.exe` by name.

For `npm run dev:refresh`, distinguish CLI process-refresh completion from durable connector
acceptance. Exit 0 with `DEV_UI REFRESHED` is valid when every exact component
receipt is fresh and the only remaining gate is external connector freshness/ACK; the same
line must still report `activation=VERIFYING admission=closed fully_ready=false
connector=pending`. Verify that malformed contract identity, stale/failing
component health, PID/epoch/revision/workspace/device mismatch, or projection
failure still returns non-zero. After current-process discovery or an eligible
compatibility bootstrap has been officially acknowledged, separately capture
the transition to `READY`, admission open, the exact connector freshness mode
and receipt timestamp, and `fullyReady=true`. A release gate that specifically
requires strict rediscovery remains open until its own strict receipt exists.

In the Command Center, capture the three loaded-source receipts for Electron UI,
Recovery Host, and Coding MCP, the separate Tunnel health state, and any
source-update notice. Service availability, Tunnel readiness, and `fullyReady`
do not override a `STALE` component receipt. Capture receipt time/age and
telemetry freshness with the status. Missing or stale telemetry keeps component
health `UNKNOWN`; it does not establish a stopped component. Report
`Stopped`/`OFF` only from a fresh explicit false receipt, and require separate
exact identity and authority before any service operation.

Interpret connector status from a recognized current `connectorContractState`
and consistent receipt fields. An absent or unrecognized enum remains
`UNAVAILABLE`; a legacy `connectorRefreshRequired` boolean alone cannot establish
acknowledgement or freshness. An acknowledged enum with acknowledgement still
pending is contradictory and also remains unavailable until reconciled.

A persisted matching SHA may retain `UNCHANGED_ACKNOWLEDGED` across process
restart without forcing contract rediscovery. That retained contract ACK does
not prove freshness for a new activation epoch or make the runtime fully ready.
Verify an official current-process discovery or eligible no-workspace
compatibility bootstrap and ACK bound to the current process/server/epoch,
exact SHA, and receipt timestamp. For a changed SHA, require discovery or the
explicitly supported exact-predecessor compatibility path. A matching or
persisted hash alone cannot close the activation gate.

## 6. Recovery plane checks

For recovery-related releases confirm Recovery Host ownership, bounded Windows Recovery Supervisor behavior, independent Recovery MCP identity, distinct Recovery Tunnel identity when configured, `recovery_plane_mode=independent_mcp_tunnel_v1`, confirmed bounded repair surface, and appropriate packaged Windows/login/fault-matrix proof.

## 7. Measurement and routing claims

Separate representative/benchmark/synthetic provenance, report sample size/strata, use provider-reported or measured facts, never present internal estimated credits as billing, and require explicit host-turn -> run/wave identity for host-visible latency claims. One successful explicit canary does not promote automatic routing.

## 8. Security and documentation consistency

Review artifacts for MCP/tunnel/recovery/loopback tokens, credentials, Authorization headers, `.env`/secret-store contents and raw sensitive provider/workspace telemetry. Confirm thin-proxy/single-Runtime authority remains intact.

Maintained product documents must agree: `docs/CURRENT_STATE.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `SECURITY.md`, and this checklist. Dated `docs/research/*` remains historical chronology/evidence.

## 9. Windows packaging

The current Electron Builder target is Windows NSIS:

```powershell
npm run dist
npm run dist:dir
```

Output root is `dist\`. `package.json` currently names the installer `coding-tools-mcp-setup-${version}.${ext}` and uses `scripts/verify-packaged-resources.js` as `afterPack`. Verify bundled resources and packaged behavior from the exact accepted source.

For Recovery changes, `npm run test:recovery:packaged` is the safe isolated packaged-runtime lane. It intentionally does not install/uninstall the Windows Recovery Supervisor Scheduled Task and therefore does not replace an installed-logon/session smoke when that OS boundary is part of the release.

After `npm run dist` creates the exact NSIS candidate, run
`node scripts/installed-recovery-smoke.js` on a machine with no existing
per-user Coding Tools MCP installation. The harness installs into an isolated
temporary path, reuses the packaged Recovery/contract smoke against the
installed tree, uninstalls in a guarded `finally` path, and verifies that the
production Recovery descriptor and existing Recovery Supervisor Scheduled Task
definition remain unchanged. This is same-machine isolated-install evidence;
do not label it new-machine, upgrade, reboot/logon, publication, or production
proof.

## 10. Post-package smoke and publish

On a safe local workspace verify Desktop startup, Recovery Host/primary MCP/Tunnel/Execution Hub, `smart-v3` connector freshness, one Runtime authority, Codex Desktop thin-proxy behavior if in scope, independent Recovery MCP/Tunnel, a safe read-only workflow, and secret-free logs.

Only after explicit authorization: accept/review exact source, commit/tag without rewriting unrelated history, build from that source, verify artifact identity/smoke, publish only the authorized artifact, verify downloaded bytes/version, and record rollback evidence. Never move a published tag or force-push merely to make history look linear.
