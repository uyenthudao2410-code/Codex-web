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

## 3. Focused source validation

Use the smallest relevant lane:

```powershell
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run test:recovery:packaged
npm run canary:opencode-flash:preflight
```

`npm run canary:opencode-flash` performs real provider dispatch and may incur external cost; run only with explicit authorization. Rust/LSP changes use the smallest affected Rust tests required by `AGENTS.md`.

## 4. EOCL and proof integrity

- A green test is not final acceptance by itself; an `ACCEPTING` wave still needs authorized accept/reject.
- Do not accept proof from an older source/worktree fingerprint.
- Check active commands, background operations, provider/agent lanes and write lease before lifecycle operations.
- Preserve canonical evidence in `.coding-tools/orchestration/ledger.sqlite3`; do not manually edit evidence to make a release look clean.

## 5. Controlled activation boundary

Runtime-affecting source tests do not prove the current process loaded new code. Use supported controlled activation and verify expected reconnect, new process/server instance identity, unchanged workspace identity, intended revision/contract, and preserved fail-closed authority state. Do not substitute `taskkill` of the serving MCP for supervised restart.

Operator `restart` and accepted code/revision activation use the durable
`full_clean_activation` path. It creates a new `activation_epoch_id`, closes
admission, checkpoints durable state, stops Electron UI/Coding MCP/Tunnel and
the configured Recovery MCP/Tunnel, hands off to a replacement Recovery Host,
then requires a final census with matching epoch, workspace, device, revisions,
fresh process identities, real Tunnel health, UI/Recovery Plane health, and a
fresh connector discovery/ACK before `fullyReady=true` can return. Automatic
fault recovery remains `soft_recovery`; it must refuse any newer disk revision
under an older epoch and may not be used as code-update proof.

If the previous activation failed after Coding MCP stopped, verify that an
explicit retry first records a fresh independent Backup-API/query-only ledger
census, rejects active mutation/managed-process or dangerous acceptance state,
and compares a second census while the application ledger gate remains
exclusive through durable epoch creation. A changed ledger hash,
workspace/source checkpoint, or runtime-state PID must fail closed without
stopping a new component set.

For development Electron changes, exercise the deterministic lifecycle with mocked tests first, then—only when local service operation is authorized—use `npm run dev` or `npm run dev:replace`. A stale UI must carry the exact checkpoint/run/wave/proof/accepted-HEAD identity from an eligible `auto_activation.closure_input`; capture the typed refusal if that durable authority is absent, incomplete, invalid, or does not own `electron_ui`. Record the exact development installation, old/new UI instance where replacement is expected, PID, runtime mode, and `running_revision == disk_revision`. `npm start` focusing an existing window is not activation evidence. Use `npm run dev:stop` for a graceful UI-only stop; require an observable exact Recovery Host at entry and either its `MISSING` UI receipt or proof that the prior exact PID exited. Confirm Recovery Host/MCP/Tunnel preservation and watchdog suppression rather than killing `electron.exe` by name.

In the Command Center, capture the three loaded-source receipts for Electron UI, Recovery Host, and Coding MCP, the separate Tunnel `READY`/`STOPPED` health state, and any source-update notice. Service availability, Tunnel readiness, and `fullyReady` do not override a `STALE` component receipt. Connector status should be interpreted from `connectorContractState` when available; when both that enum and the legacy `connectorRefreshRequired` boolean are absent, the truthful state is `UNAVAILABLE`, not acknowledged. An unchanged acknowledged SHA survives process restart, while a changed SHA requires the discovery/acknowledgement sequence.

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

## 10. Post-package smoke and publish

On a safe local workspace verify Desktop startup, Recovery Host/primary MCP/Tunnel/Execution Hub, `smart-v3` connector freshness, one Runtime authority, Codex Desktop thin-proxy behavior if in scope, independent Recovery MCP/Tunnel, a safe read-only workflow, and secret-free logs.

Only after explicit authorization: accept/review exact source, commit/tag without rewriting unrelated history, build from that source, verify artifact identity/smoke, publish only the authorized artifact, verify downloaded bytes/version, and record rollback evidence. Never move a published tag or force-push merely to make history look linear.
