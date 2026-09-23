# HTTP server shutdown drain fix — 23/09/2026

**Observed:** 2026-09-23
**Workspace:** `E:\DEV\Codex-web`
**Source before this wave:** `main@697a523a`
**Scope:** eliminate the Windows HTTP-test/runtime teardown race without
weakening the ledger gate or changing acceptance authority. This is a focused
reliability checkpoint, not a Problem-closure receipt.

## 1. Reproduction

Running the execution-hub HTTP suites consecutively reproduced a real
reliability failure:

```text
tests/test_execution_hub.py tests/test_execution_hub_faults.py
1 failed, 1 teardown error
```

The failing request was `provider_observe`. The client timed out while the
server still had a request handler active. Teardown then failed to remove the
temporary workspace because Windows still held the canonical ledger file:

```text
TimeoutError: timed out
PermissionError: [WinError 32] ... orchestration\\ledger.sqlite3
```

The same provider test passed in isolation, which identifies a lifecycle race
between consecutive `RuntimeHTTPServer` instances rather than a deterministic
provider protocol rejection.

## 2. Typed cause and source change

`RuntimeHTTPServer` used daemon request threads but `server_close()` closed the
shared `Runtime` immediately. The previous close order could therefore close a
SQLite-backed runtime while a handler thread still owned a ledger connection.

`coding_tools_mcp/mcp_http_handler.py` now:

1. tracks each request thread;
2. rejects new requests once shutdown begins;
3. performs a bounded request-thread drain;
4. closes the session manager and shared `Runtime` only after the drain;
5. preserves daemon-thread behavior for the long-lived MCP server.

This does not alter ledger schemas, lock timeouts, acceptance gates, provider
authority, or client discovery semantics.

## 3. Focused proof after the change

```text
python -m py_compile coding_tools_mcp/mcp_http_handler.py
  PASS

provider/telemetry focused tests
  3 passed, 14 deselected

python -m pytest -q tests/test_execution_hub.py tests/test_execution_hub_faults.py
  22 passed, 4 subtests passed
  0 failed
  0 teardown errors
```

The combined suite completed in approximately 66 seconds after the fix. This
is stronger than the prior isolated pass, but it is not yet a full
`npm run test:mcp` acceptance result.

## 4. Acceptance boundary that remains unchanged

The two Problems remain separate and `OPEN`. This fix only removes a local
HTTP/runtime shutdown race. It does not prove:

```text
strict current-client tools/list/server/discover = NOT_PROVEN
real attested workspace_context                = NOT_PROVEN
reboot/logon/Machine B                         = NOT_RUN
natural C01-C12 outcome                        = NOT_PROVEN
natural BG01-BG14 Goal outcome                 = NOT_PROVEN
independent outcome receipts                   = 0
closure authority                              = NOT_AVAILABLE
```

The next reliability action is a full Python/MCP suite run. If it remains
green, the source-side flake is closed at this layer; client discovery and
natural-work gates must still be completed independently.
