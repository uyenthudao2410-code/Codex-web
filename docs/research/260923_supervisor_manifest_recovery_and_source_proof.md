# Supervisor manifest recovery and current source proof — 23/09/2026

**Observed:** 2026-09-23 15:14:17 +07
**Workspace:** `E:\DEV\Codex-web`
**Source:** `main@697a523a`
**Scope:** classify the post-build runtime failure, repair the supported
Supervisor installation boundary, and record the strongest source/package
proof available before strict client acceptance. This is not a Problem-closure
receipt.

## 1. Failure reproduced after package/test wave

After the recovery E2E, packaged build and isolated installer smoke, the live
development status regressed to:

```text
state=MISSING
host=unavailable
installation=unknown
runtime_update_incomplete=unknown
connector_state=UNAVAILABLE
error_code=RECOVERY_DESCRIPTOR_STALE
```

The supported Supervisor status identified the typed cause:

```text
state=spawn_failed
last_error_code=SPAWN_FAILED
last_error_message=Recovery Supervisor executable missing.
consecutive_failures=7
```

The installed Supervisor manifest still pointed at the packaged executable
under `C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP`, but that
production executable was absent. The directory contained only a leftover
`resources` directory. The previous isolated NSIS smoke had installed and
uninstalled only its temporary target and verified that the production
descriptor/task were unchanged; it did not provide a production executable.

This was classified as an installed Supervisor manifest/target drift, not as
ledger corruption, a source revision mismatch, or a reason to delete/kill a
process by name.

## 2. Supported repair and controlled activation

The supported installer boundary was used:

```text
npm run recovery:supervisor:install
```

The resulting manifest was verified without printing credentials:

```text
mode=development
app_root=E:\DEV\Codex-web
executable=E:\DEV\Codex-web\node_modules\electron\dist\electron.exe
executable_exists=true
task_name=WebMCP Recovery Supervisor
```

The Supervisor then reported:

```text
task_state=Running
state=healthy
consecutive_failures=0
last_error_code=none
last_host_instance_id=6b978f77cc17121efa42ba0e1a4a2988
control_plane_agent_state=running_heartbeat_only
```

The previous packaged executable was not restored by copying bytes or by
editing the manifest manually. The supported install command replaced the
Supervisor registration and selected the current development checkout.

The lifecycle authority was then used once:

```text
npm run dev:refresh
```

Result:

```text
activation=READY
epoch=activation-mudtsrpx-8276eb00eebd2b53d4069f5ad1c0172f
host=6b978f77cc17121efa42ba0e1a4a2988
ui=432ab5f5a415c413b0c182fab7ed87a4
mcp=ready
tunnel=not-required
admission=open
fully_ready=true
connector_state=CHANGED_NEEDS_DISCOVERY
```

## 3. Current runtime and ledger readback

`npm run dev:status` now reports:

```text
state=CURRENT
host=available
installation=current
running_revision=2194e8a2bdc174c3f83df9edd3d944a5ad5cccdfb6f7e5da7dc699060a63a94c
mcp_revision_state=current
mcp_running_revision=a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
mcp_disk_revision=a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
components_ready=true
fully_ready=true
runtime_update_incomplete=false
connector_state=CHANGED_NEEDS_DISCOVERY
connector_rediscovered=false
connector_refresh_required=true
connector_ack_pending=false
```

Authenticated Recovery IPC returned:

```text
status=OBSERVED
workspace_matched=true
authority_granted=false
live_accepted=false
host_pid=32304
host_instance_id=6b978f77cc17121efa42ba0e1a4a2988
mcpRunning=true
nativeAlive=true
tunnelRunning=false
componentsReady=true
fullyReady=true
centralConnected=true
authorityReady=true
updateIncomplete=false
identity_current=true
process_instance_id=7vAHdA8bZ4q6uCwN
server_instance_id=UOJ1ZIJNfWTA65Ef
tool_contract_sha256=bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0
activation_state=READY
admission_open=true
connector_rediscovered=false
client=null
```

The query-only Backup-API census remains:

```text
schema_version=12
integrity_check=ok
foreign_key_check_rows=0
mutated_canonical_ledger=false
projection=CONTEXTUAL_PROJECTIONS
projection_drift=false
context_count=1079
ordinary_active_runs=17
p5_epochs=6
unexplained_active_runs=0
unbound_live_resource_residues=0
stale_background_operation_residues=0
physical_snapshot_sha256=6ce564577e1bdea186c3cad483d8cbe85584eee6ae55e86b343fc6c3a04f8fc9
logical_snapshot_sha256=8bca8afdf22dd321226d284cf055f9675528aa226cc259eee0083bde92155254
```

## 4. Source, recovery and package proof

The following checks were run against the current source tree or a package
derived from it:

```text
npm test
  Node/Electron: 1033 passed, 0 failed
  source root clean
  repository secret check: PASS

npm run test:recovery:e2e
  3 passed, 0 failed

npm run test:recovery:packaged
  packaged directory smoke: PASS
  required resources: 17
  smart-v3 tools: 8
  MCP alive: true
  Supervisor healthy: true
  live-owner/hash mismatch guards: PASS

npx electron-builder --win nsis
  NSIS installer built successfully

node scripts/installed-recovery-smoke.js
  isolated install/register: PASS
  installed packaged smoke: PASS
  uninstall: PASS
  installed files removed: true
  production descriptor stable: true
  scheduled task definition stable: true
```

The Python/MCP suite result was:

```text
1161 passed, 5 skipped
```

One test failed only in the 32-minute full-suite run:
`ExecutionHubFaultTests.test_chatweb_accept_reclaims_expired_explicit_historical_run`.
The failure was an HTTP timeout followed by a Windows SQLite temporary-file
teardown lock. The test passed when run alone and when run with
`test_execution_hub.py` (`22 passed, 4 subtests`). It is therefore recorded as
a full-suite resource/concurrency flake, not as a confirmed deterministic
product regression. It should remain a CI reliability item until a full run is
green without the flake.

## 5. Remaining acceptance boundary

The supported client surface is still unavailable (`Codex auth token is
unavailable`), so the following remain unproven:

```text
STRICT tools/list/server/discover       = NOT_PROVEN
CLIENT_DISCOVERY_PROVENANCE             = NOT_PROVEN
CLIENT_DELIVERY_CONFIRMATION            = NOT_PROVEN
REAL workspace_context                   = NOT_PROVEN
BOOT_BEFORE_AFTER                        = NOT_PROVEN
REBOOT / LOGON / MACHINE B               = NOT_RUN
PACKAGE_EXECUTABLE_SUPERVISOR_HASHES    = NOT_PROVEN for production install
NATURAL C01-C12 OUTCOME                  = NOT_PROVEN
NATURAL BG10/BG14 OUTCOME                = NOT_PROVEN
Problem closure authority                = NOT_AVAILABLE
```

`fully_ready=true` is now genuine for the current development central runtime,
but `connector_state=CHANGED_NEEDS_DISCOVERY`, `client=null`, and
`authority_granted=false` keep the external acceptance gate fail-closed.

## 6. Exact next action

1. With a supported authenticated client, collect current `tools/list` and
   `server/discover` and bind both receipts to the epoch, process/server
   identities and contract SHA above.
2. Call a real attested `workspace_context` on `E:\DEV\Codex-web`.
3. Only after that proof, run the reboot/logon, Machine B and fault matrices.
4. Run one natural C01-C12 Problem and one natural BG01-BG14 Goal, capture
   independent outcomes and build exact coverage manifests.
5. Resolve the full-suite Python concurrency flake before release-level
   acceptance; do not relabel the isolated pass as a full-suite pass.

The two Problems remain separate and OPEN. This wave fixed the concrete
Supervisor executable/manifest drift and restored the controlled development
runtime; it did not fabricate client discovery, natural work, or closure.
