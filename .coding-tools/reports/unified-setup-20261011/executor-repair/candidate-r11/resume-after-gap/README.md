# Same-candidate r11 resume after the operator gap

Root owns live operations. This directory prepares one exact packaged r11 Recovery Host launch under `web-mcp-assistant`, preserving the old acceptance RUN/WAVE. It does not replay full-clean refresh, install a task/service, alter product source, or reuse an old agent marker.

## Root sequence

Use this directory's absolute `resume.cjs` path. `preflight` verifies HEAD, the frozen 12-file source/package parity, all four old component PIDs absent, exact old descriptor, persisted central READY proof, canonical idle census, unchanged pending records, no package process, zero VM, and current parent Job limits.

```powershell
node $helper preflight
node $helper activate --operator-approved-r11-resume --helper-sha256=<helper_sha> --server=<fresh_closed_receipt> --server-sha256=<receipt_sha>
node $helper status
node $helper policy --operator-approved-r11-resume --helper-sha256=<helper_sha> --server=<fresh_closed_receipt> --server-sha256=<receipt_sha> --renewal=<new_approved60m_receipt> --renewal-sha256=<renewal_sha>
node $helper agent --operator-approved-r11-resume --helper-sha256=<helper_sha> --server=<fresh_closed_receipt> --server-sha256=<receipt_sha> --renewal=<new_approved60m_receipt> --renewal-sha256=<renewal_sha>
```

Each mutation requires a fresh exact server recovery/quiescence receipt. Policy and agent additionally require the newly approved 60-minute window after the expired `1791734596302` window. Runtime and agent each reserve a durable exclusive one-attempt file before launch. A failed launch or ambiguous child Job result requires root reconciliation; there is no automatic repeat.

`breakaway-launch.py` uses the supported packaged `--recovery-host` CLI with hidden startup and `CREATE_BREAKAWAY_FROM_JOB | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`. It verifies allowed current Job flags before creation and verifies the child is outside a Job afterward. Access denied fails closed. The new descriptor is adopted only when installation, PID/start token, and authenticated ping match the recorded spawned identity. Existing product startup behavior remains authoritative; a READY claim still needs a fresh live status.

The finite agent iteration count is derived from the remaining approved interval, using the product's supported connected-agent CLI. It is an iteration cap, not a hard wall-clock expiry: action authority remains separately bounded by the server context/pilot. Agent stderr is discarded, and protected credentials are neither copied nor emitted.

## Evidence

Read-only inventory found no supervisor manifest for this profile; the exact Scheduled Task query was unavailable, so task absence is unproven. The current Python tool process was Job-associated with flags `10240` (`0x2800`: breakaway allowed and kill on close). This establishes a launch lifetime risk in the current tool context, not the cause of the previous disappearance. These observations are stored in `diagnostic-receipt.json`.

`proof-receipt.json` records seven focused offline checks. Live launch, descriptor adoption, policy sync, heartbeat, and final MCP acceptance remain root's next work. Git stays dirty `main @ 2c554f59`; no commit/push/deployment/service/task installation or runtime launch was performed by this preparation lane.
