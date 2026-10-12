# Windows r4 activation checkpoint

Observed 11/10/2026, **15:35:54 +07**. Operator authorized r4 activation, the same Tools-Codex-web scope for 60 minutes, and no Windows reboot.

## Result

Activated unpacked candidate `dist/windows-candidate-mxc-wsb-cbe1774-mcp-feedback-1011-r4/win-unpacked` for `%APPDATA%/web-mcp-assistant`. The supported full-clean refresh committed a new durable `READY` epoch with admission open; `fullyReady`, `localReady`, `componentsReady`, `centralConnected`, and `authorityReady` were all true and `updateIncomplete` was false.

- Installation: `1567083269469e2926937314b22ae945c28e61ca93ffee9c28ab9d3f88e955f1`
- Epoch: `activation-mv3kgpod-d9dec64ec4eeeffe5f6e764313648af5`
- Operation: `full-clean-mv3kgg5n-7381ab1c7f0bfa6cd7077e7c`
- READY commit: `1c49a3cb2232e545b306cc33ee29d6acd50f141cafc78c28b1eed19f56f0eec5`
- READY committed: `2026-10-11T08:34:25.652Z`
- Coding MCP running and disk revision: `63b08970ce899e7e950b2acb444369048921057234c8ef55f0719108c6922390` (148 files, current, matching epoch).
- Packaged node agent SHA-256: `3f044fd7883412c54d58fb54755d54dd133810ec0687c32efc6a41f96c23e8c2`.
- Packaged app.asar SHA-256: `52a267375bd449c2f2f630814a1fc6382dd683fe8948fa2dd2728dacf1df365a`.

## Exact process observations

| Role | PID | Windows process start token | Observation |
| --- | --- | --- | --- |
| Recovery Host | 6388 | 134361812356824390 | Authenticated r4 descriptor and fresh IPC status |
| Electron UI | 4784 | 134361812341558990 | OS identity live; registered, healthy, matching installation |
| Coding MCP | 28604 | 134361812379914820 | OS identity live; r4 module root, matching revision and epoch |
| Connected node agent | 18876 | 134361809362680020 | r4 packaged Python/node_agent; iteration 25 completed, heartbeat succeeded |

The connected agent is bounded to 200 iterations with 15-second interval and 60-second maximum reconnect backoff. It was started at 15:28:56 +07. No permanent supervisor or scheduled task was installed. Capability lane logs contain action IDs and state summaries, with no file contents or credentials.

## Authority and remaining gate

Metadata assignment installed through the supported packaged service for workspace `workspace_dda1d78e9a21402aa6213f72af64f788`, generation `generation_c2f13e8d02344cf6a38a3f42ecfa59b6`, with expiry **16:26:24.008 +07** (`1791710784008`). The assignment receipt reported `windows_acl_verified=false`; this is recorded without changing the authority guard. Existing matching standing file-read and approved-patch policies remain enabled. Their standing-policy expiry semantics were not rewritten.

Execution policy remains absent. The supported sandbox probe returned `WINDOWS_SANDBOX_NOT_READY`; WindowsSandbox.exe is absent after the previously enabled feature reported that a reboot was needed. No fallback command was launched and no Windows reboot occurred. This checkpoint proves local readiness and remote read admission, not successful sandboxed execution.

## Preservation and failures

The r3 Recovery Host PID 12036, native PID 21736, UI PID 20308 and previous node agent PID 10668 were already absent at preflight; their prior exit cause was not observed. The stale descriptor was preserved until normal r4 startup replaced it. Candidate hashes were revalidated before launch.

The first exclusive stopped-runtime census passed with all active command/background/managed-process/agent-lane counts zero, 17 classified stale candidates, and one awaiting-acceptance RUN `95e909f0040a448faa9f1f3257e2ee2c`. `allowAcceptancePending=true` preserved that acceptance boundary; the census did not mutate the canonical ledger. No proof, acceptance, lease or orchestration record was fabricated or manually edited.

The first full-clean refresh and the following standalone census exceeded the existing 30-second census deadline. A content-free diagnostic showed snapshot copy/integrity/facts/hash complete at 4.672 seconds, 1,083 contextual projections complete at 19.875 seconds, and classification at 19.906 seconds. A subsequent normal admission census passed in 6.63 seconds. One full-clean retry then reached HANDOFF and the new READY epoch. The deadline and guard were unchanged. Earlier failures remain in the JSONL receipt.

The first connected-agent launch supplied an unsupported `--data-root` override; packaged admission refused it before heartbeat. Only that exact owned PID/start-token was terminated. The override was removed and the replacement used the supported profile-derived data root. Subsequent heartbeat and lane observations succeeded.

## Files and next action

- `windows-activation.cjs`: supported activation, policy installation, bounded agent launch, and sanitized proof helper.
- `windows-activation.jsonl`: chronological preflight, failures, census, activation, policy and final proof receipts.
- `windows-activation-agent.stdout.jsonl` / `.stderr.log`: bounded agent output.
- `windows-activation-census-diagnose.py` and `windows-activation-census-diagnose-result.json`: read-only latency evidence.

Primary repository remains dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`; this workstream performed no staging, commit or push. Windows service/runtime operations occurred as authorized; Windows was not rebooted. No additional refresh or census is needed for this activation. Root controller continues the prepared MCP read/error/status proof while the bounded agent remains available.
