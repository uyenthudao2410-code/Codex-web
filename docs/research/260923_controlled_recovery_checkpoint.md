# Controlled recovery checkpoint after UI-missing state — 23/09/2026

**Observed:** 2026-09-23 14:13:48 +07
**Workspace:** `E:\DEV\Codex-web`
**Source at checkpoint:** `main@661bafab` (`docs: record controlled recovery activation`)
**Purpose:** record the controlled recovery performed after the post-delivery
readback reported `dev:status state=MISSING`. This is a runtime checkpoint, not
a Problem-closure receipt.

## 1. Trigger and classification

Immediately after commit `661bafab` was pushed, the lifecycle status was:

```text
state=MISSING
host=available
installation=current
pid=36568
running_revision=none
disk_revision=2194e8a2bdc174c3f83df9edd3d944a5ad5cccdfb6f7e5da7dc699060a63a94c
mcp_revision_state=current
mcp_update_pending=false
components_ready=true
fully_ready=true
runtime_update_incomplete=false
connector_state=CHANGED_NEEDS_DISCOVERY
connector_rediscovered=false
connector_refresh_required=true
```

The referenced UI PID was no longer present. The authenticated Recovery IPC
readback still showed a live Recovery Host/MCP, so this was classified as a
stale/missing Electron UI process projection, not as a source revision mismatch
and not as permission to kill processes manually.

## 2. Controlled recovery execution

The existing lifecycle authority was used:

```text
npm run dev:refresh
```

The command first reconciled the previous state and then completed a fresh
full-clean activation:

```text
DEV_UI REFRESH RECONCILE action=full_clean
previous_host=8e8300a51dc72625164ea9eef7c7dbac
previous_ui=none
services=RecoveryHost,CodingMCP,CodingTunnel,RecoveryMCP,RecoveryTunnel,ElectronUI

DEV_UI REFRESHED action=full_clean
epoch=activation-mudrn9pa-ab77cbc8628a804b0bf3aadead36f75e
activation=READY
host=18c95fc79eb4ccf102d1b824a0868a0a
ui=97587301f35cf3cec7532c691113dcc0
mcp_pid=37044
tunnel_pid=unknown
mcp=ready
tunnel=not-required
admission=open
fully_ready=true
connector=pending
connector_state=CHANGED_NEEDS_DISCOVERY
```

No direct process termination, JSON edit, SQLite edit, manual connector ACK,
or worktree was used.

## 3. Post-recovery live status

`npm run dev:status` now reports:

```text
state=CURRENT
host=available
installation=current
pid=26856
instance=97587301f35cf3cec7532c691113dcc0
running_revision=2194e8a2bdc174c3f83df9edd3d944a5ad5cccdfb6f7e5da7dc699060a63a94c
disk_revision=2194e8a2bdc174c3f83df9edd3d944a5ad5cccdfb6f7e5da7dc699060a63a94c
mcp_revision_state=current
mcp_running_revision=a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
mcp_disk_revision=a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
components_ready=true
fully_ready=true
runtime_update_incomplete=false
runtime_signal_stale=false
connector_state=CHANGED_NEEDS_DISCOVERY
connector_rediscovered=false
connector_refresh_required=true
connector_ack_pending=false
```

An authenticated Recovery IPC observation at the same wave returned:

```text
status=OBSERVED
source=authenticated_recovery_ipc
workspace_matched=true
authority_granted=false
live_accepted=false
host_pid=36480
host_instance_id=18c95fc79eb4ccf102d1b824a0868a0a
recovery_host_revision=b6a248ade62fe7e9516d761b3d7903310d1f12adb4660616c7f71a78af7fa019
coding_mcp_revision=a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
mcpRunning=true
nativeAlive=true
tunnelRunning=false
componentsReady=true
fullyReady=true
updateIncomplete=false
identity_current=true
activation_state=READY
admission_open=true
process_instance_id=97LjvZ_NEKksr-hK
server_instance_id=ymHv95kHXygeJZLJ
tool_contract_sha256=bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0
connector_rediscovered=false
connector_refresh_required=true
client=null
```

`OBSERVED` is an authenticated readback only. It is not a strict client
discovery receipt, a schema-v2 reboot receipt, or acceptance. The observation
continues to list the following missing evidence:

```text
REAL_CLIENT_WORKSPACE_READ
CLIENT_DELIVERY_CONFIRMATION
CLIENT_DISCOVERY_PROVENANCE
BOOT_BEFORE_AFTER
PACKAGE_EXECUTABLE_SUPERVISOR_HASHES
CENTRAL_BINDING_POLICY_RECEIPT
ATTEMPT_HISTORY_STARTUP_INTENT
```

## 4. Ledger and projection readback

The query-only Backup-API census immediately after recovery reports:

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
physical_snapshot_sha256=fbc9bd66c5494cd1fcc65c5cb3c89da2ee1202703020914545cf2951a950a0d2
logical_snapshot_sha256=af3082a262f52bbf541f0cba1cc680ebe767ddd32707d1f283d7215e4fc2e8de
```

The canonical ledger remains query-only and integrity-valid. Runtime evidence
continued to move after the earlier delivery snapshot; that is expected live
telemetry drift, not a manual ledger mutation.

## 5. Advancement and remaining boundary

```text
SOURCE_PRESENT                   = PASS
FOCUSED_PROOF                    = PASS
DELIVERED_MAIN                   = PASS (661bafab pushed)
PACKAGED_SMOKE_CURRENT_HEAD      = PASS (isolated evidence)
CONTROLLED_ACTIVATION            = PASS (fresh epoch)
CONTROLLED_UI_RECOVERY           = PASS (MISSING -> CURRENT)
CURRENT_PROCESS_IDENTITY         = PASS via authenticated Recovery IPC
STRICT tools/list/server/discover = NOT_PROVEN
REAL workspace_context            = NOT_PROVEN
REBOOT / LOGON / MACHINE B        = NOT_RUN
NATURAL C01-C12 OUTCOME           = NOT_PROVEN
NATURAL BG10/BG14 OUTCOME         = NOT_PROVEN
Problem closure authority         = NOT_AVAILABLE
```

The recovery closes the immediate UI-process outage for this controlled epoch;
it does not close either Problem. Both `prl-22e670302757c9b7663170e226ed7c26`
(C01-C12) and `prl-e918c7d33e70c2d304d0797e11b05fcb` (BG01-BG14) remain OPEN
until their independent client, reboot, natural-use, and outcome gates are
proven.

## 6. Next safe action

1. Use a supported authenticated client surface to collect current
   `tools/list` and `server/discover`, bound to the new epoch, process/server
   identities, and `tool_contract_sha256`.
2. Call a real attested `workspace_context` for `E:\DEV\Codex-web` and require
   exact workspace/endpoint/generation binding.
3. Only after those receipts, run reboot/logon, Machine B, fault-matrix, and
   natural Problem/Goal outcome gates.

If the connector remains unavailable or the bounded epoch expires, create a new
controlled lifecycle epoch rather than extending the old one or fabricating an
ACK.

**Operator checkpoint:** the controlled recovery repaired the observed UI
`MISSING` state and restored `CURRENT/READY/OPEN`. The remaining blocker is
external client discovery/attestation and natural outcome proof, not basic
Recovery Host/MCP startup.
