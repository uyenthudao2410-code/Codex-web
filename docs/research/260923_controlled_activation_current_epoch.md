# Controlled activation current epoch — 23/09/2026

**Observed:** 2026-09-23 14:05:30 +07
**Workspace:** `E:\DEV\Codex-web`
**Source at activation:** `main@d4b0d02c41302ae828c541d20097469f92d038e3`
**Operation:** controlled `npm run dev:refresh` through the existing lifecycle
authority. This is a runtime evidence snapshot, not a closure receipt.

## 1. Controlled refresh result

Command:

```text
npm run dev:refresh
```

The lifecycle command passed its exact installation/epoch preflight and
postflight:

```text
DEV_UI REFRESHED
action=full_clean
epoch=activation-mudrb7ef-4d453ea9d8de8068b09dac397927a0c1
activation=READY
host=8e8300a51dc72625164ea9eef7c7dbac
ui=7a04e4b25005dd71e4ffbbc787191fea
mcp_pid=31856
mcp=ready
tunnel=not-required
admission=open
fully_ready=true
connector=pending
connector_state=CHANGED_NEEDS_DISCOVERY
```

The operation created a fresh full-clean refresh epoch with
`source_checkpoint=null` and `allow_acceptance_pending=true`. This is a
controlled process/runtime activation, not an accepted-code checkpoint and not
a connector ACK.

## 2. Current authenticated Recovery IPC observation

Command:

```text
node scripts/collect-boot-runtime-observation.js --workspace E:\DEV\Codex-web
```

Result was `status=OBSERVED`, with no client contact adopted:

```text
source                    = authenticated_recovery_ipc
workspace_matched         = true
authority_granted         = false
live_accepted             = false
host_pid / host_instance  = 38944 / 8e8300a51dc72625164ea9eef7c7dbac
runtime_mode              = development
recovery_host_revision    = b6a248ade62fe7e9516d761b3d7903310d1f12adb4660616c7f71a78af7fa019
coding_mcp_revision       = a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
mcpRunning / nativeAlive  = true / true
tunnelRunning             = false (tunnel not required for central_executor)
componentsReady           = true
fullyReady                = true
localReady                = true
centralConnected          = true
authorityReady            = true
updateIncomplete          = false
identity_current          = true
activation_epoch          = activation-mudrb7ef-4d453ea9d8de8068b09dac397927a0c1
activation_state          = READY; admission_open=true
process_instance_id       = 0TZYuuh-ViBzRQIc
server_instance_id        = oABtBptwL6TJAFEx
tool_contract_sha256      = bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0
connector_rediscovered    = false
connector_refresh_required= true
connector_state           = CHANGED_NEEDS_DISCOVERY
client                    = null
```

The reader explicitly reports these missing items:

```text
REAL_CLIENT_WORKSPACE_READ
CLIENT_DELIVERY_CONFIRMATION
CLIENT_DISCOVERY_PROVENANCE
BOOT_BEFORE_AFTER
PACKAGE_EXECUTABLE_SUPERVISOR_HASHES
CENTRAL_BINDING_POLICY_RECEIPT
ATTEMPT_HISTORY_STARTUP_INTENT
```

It also explicitly says the observation is readback only and is not a schema-v2
reboot receipt. No stale client contact was reused.

## 3. Ledger/projection state after activation

The read-only Backup-API census at `2026-09-23T07:05:46.308Z` reports:

```text
schema / integrity / FK          = 12 / ok / 0
mutated_canonical_ledger         = false
projection / drift               = CONTEXTUAL_PROJECTIONS / false
context_count                    = 1079
ordinary_active_runs             = 17 (all THRESHOLD_SENSITIVE_STALE_CANDIDATE)
p5_epochs                        = 6
unexplained / unbound / stale-bg = 0 / 0 / 0
physical snapshot SHA-256        = 89d729096d281351fe12487dbd680aa8b4ca6b97d5b5fbcd830cd7f3b384963b
logical snapshot SHA-256         = de4eb635ba605b853964730b9ce2f4c95bee6730fe053f111b69c3eab121d79d
```

The activation epoch stores an earlier immutable start snapshot. Later runtime
events changed the live ledger snapshot hash; this is recorded as normal
post-activation evidence drift and was not manually edited. The census still
proves integrity/FK and `mutated_canonical_ledger=false`.

## 4. Exact advancement and remaining boundary

```text
SOURCE_PRESENT                 = PASS
FOCUSED_PROOF                  = PASS
DELIVERED_MAIN                 = PASS
PACKAGED_SMOKE_CURRENT_HEAD    = PASS (separate isolated run)
CONTROLLED_ACTIVATION           = PASS for this current epoch
CURRENT_PROCESS_IDENTITY        = PASS via authenticated Recovery IPC
STRICT tools/list/server/discover= NOT_PROVEN
REAL workspace_context          = NOT_PROVEN
REBOOT / LOGON / MACHINE B      = NOT_RUN
NATURAL C01–C12 OUTCOME         = NOT_PROVEN
NATURAL BG10/BG14 OUTCOME       = NOT_PROVEN
Problem closure authority       = NOT_AVAILABLE
```

`fullyReady=true` here means the central runtime/lifecycle path is ready. It
does not mean the external connector has rediscovered and acknowledged the
current tool contract. The connector gate remains fail-closed by design.

The observed epoch deadline was `2026-09-23T07:13:17.312Z` (14:13:17 +07).
If no supported client completes discovery before that bounded epoch expires,
the next attempt must create another controlled epoch; do not extend the old
epoch by editing its JSON or ledger row.

## 5. Exact next action

With a supported authenticated client surface available:

1. Collect current-process `tools/list` and `server/discover` through that
   client and bind the result to the process/server/epoch/contract identities
   above.
2. Call a real `workspace_context` for `E:\DEV\Codex-web`; require the
   attested contact and exact workspace/endpoint/generation match.
3. Only after that receipt, run the reboot/logon, fault, Machine B and natural
   Problem/Goal gates.

Until then, do not ACK the connector manually, do not call a local Recovery IPC
observation a client discovery receipt, and do not close either Problem.

**Operator checkpoint:** controlled activation materially advanced the runtime
from `MISSING` to `READY/OPEN` with current process identity and healthy MCP.
The remaining blocker is now narrower: supported-client discovery/attestation
and natural outcome, not basic Supervisor/MCP startup.
