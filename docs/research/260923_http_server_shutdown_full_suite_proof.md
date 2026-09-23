# HTTP server shutdown drain — full-suite proof — 23/09/2026

**Observed:** 2026-09-23
**Workspace:** `E:\DEV\Codex-web`
**Source under test:** working tree based on `main@697a523a`
**Precondition:** [260923_http_server_shutdown_drain_fix.md](260923_http_server_shutdown_drain_fix.md)

## Result

After the `RuntimeHTTPServer` request-thread drain change, the complete Python
MCP suite was run through the repository command:

```text
npm run test:mcp
```

Terminal result:

```text
1162 passed, 5 skipped
0 failed
0 teardown errors
duration=2229.96s (0:37:09)
```

The two execution-hub modules that previously exposed the race completed as
part of the same run:

```text
tests/test_execution_hub.py
tests/test_execution_hub_faults.py
```

No `provider_observe` timeout and no Windows `WinError 32` temporary-ledger
teardown lock occurred in this full run.

## Interpretation

The source-side Python/MCP reliability gate for this race is now green. This
proves the shutdown lifecycle change across the full current Python suite; it
does not promote either Problem to closure and does not substitute for client
discovery or natural-work evidence.

Still not proven by this run:

```text
strict current-client tools/list/server/discover = NOT_PROVEN
real attested workspace_context                = NOT_PROVEN
reboot/logon/Machine B                         = NOT_RUN
natural C01-C12 outcome                        = NOT_PROVEN
natural BG01-BG14 Goal outcome                 = NOT_PROVEN
independent outcome receipts                   = 0
closure authority                              = NOT_AVAILABLE
```

The next delivery boundary is the mandatory `.coding-tools` snapshot/guard,
followed by Node/Electron validation and a local commit on `main`.
