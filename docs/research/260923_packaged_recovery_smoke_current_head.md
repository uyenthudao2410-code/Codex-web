# Packaged Recovery Host smoke — current HEAD

**Observed:** 2026-09-23 14:06 +07
**Workspace:** `E:\DEV\Codex-web`
**Source:** `main@a779e7801d80a62d09d5a9eb5c63b181edfed7a4`
**Mode:** isolated packaged smoke only. Không restart runtime development,
không reboot, không ACK connector, không sửa ledger trực tiếp.

## Command and result

```text
npm run test:recovery:packaged
```

The command rebuilt `dist/win-unpacked` and ran
`scripts/packaged-recovery-smoke.js`. Result:

```json
{
  "ok": true,
  "package": {
    "executable": true,
    "app_asar": true,
    "required_resources": 17,
    "smart_tool_contract": {
      "profile": "smart-v3",
      "tools": [
        "agent_workflow",
        "command_control",
        "document_workflow",
        "exec_command",
        "request_permissions",
        "task_control",
        "view_image",
        "workspace_context"
      ]
    }
  },
  "isolation": {
    "user_data_isolated": true,
    "production_descriptor_stable": true
  },
  "recovery": {
    "host_ready": true,
    "device_identity_present": true,
    "mode": "independent_mcp_tunnel_v1",
    "mcp_alive": true
  },
  "supervisor": {
    "healthy": true,
    "live_owner_fail_closed": true,
    "hash_mismatch_fail_closed": true,
    "scheduled_task_mutation": false
  }
}
```

Package hashes captured after the build:

```text
dist/win-unpacked/resources/app.asar
  SHA-256 = 73FBA0E273BC1B13D692A26C3E1F0F3652EADD78AA372A8008DA5D86B31A0760
  size    = 7,284,934 bytes

dist/win-unpacked/Coding Tools MCP.exe
  SHA-256 = EF9BC4D29A37F3E068B60AD0AD893E263F6A50AA6F38CE55E7DDFFE23EEE7CA1
  size    = 225,659,904 bytes

dist/win-unpacked/resources/resources/coding-tools-mcp
  files   = 223
  tree SHA-256 = 982ADC1DC9134421B661DB81A8ABE59B98D1AEAB99E531B12ED13087797BF8B2
```

The installed path previously used in historical evidence,
`E:\WebMcpAcceptanceHost-1.0.0`, currently has no `resources\app.asar`; this
smoke therefore proves only the freshly built isolated `dist/win-unpacked`
artifact, not that an installed product has been activated or is the current
user target.

## What this advances

This is current packaged evidence for the following parts of `prl-22e…` rev1:

- C01 entry point/resource/package cold-start precondition;
- C02 supervisor ownership and fail-closed live-owner guard;
- C04 exact smart-v3 public tool contract in the packaged artifact;
- C06 hash-mismatch/identity guard behavior;
- C07 packaged Recovery Host/MCP/Tunnel liveness in isolation;
- C10 packaged resource identity and descriptor stability.

It also confirms that the current source package still contains the eight-tool
contract required by the continuation path. It does **not** prove C08/C09/C11/
C12, reboot/logon, Machine B, current installed identity, client strict
discovery, real `workspace_context`, natural use, or independent outcome.

## Current boundary after smoke

```text
PACKAGED_SMOKE_CURRENT_HEAD      = PASS
INSTALLED_LIVE_ACTIVATION        = NOT_PROVEN
CURRENT_PROCESS_DISCOVERY        = NOT_PROVEN
REAL_WORKSPACE_CONTEXT           = NOT_PROVEN
REBOOT / LOGON / MACHINE B       = NOT_RUN
NATURAL C01–C12 OUTCOME          = NOT_PROVEN
```

The development runtime remains separately fail-closed (`MISSING`, primary
MCP/Tunnel stopped, connector `UNAVAILABLE`). The isolated smoke did not mutate
that runtime or the canonical ledger.

**Operator checkpoint:** packaged smoke completed successfully on the current
HEAD and supplied fresh artifact evidence. The next required action is still a
supported-client controlled activation, not a blind restart or a claim of
Problem closure.
