# Proof Metadata Ledger Closure — 2026-08-22

## Canonical control-plane boundary

- Task ID: `5e87d8d0e93e492680a6c4fb808d4da8`
- Canonical RUN ID: `f9aea53e7b084ae880bcb8a56cd93c3a`
- Operator completion report ID: `5d7e27f61baa59f8b8c900cfdb3ca6a3170caa1721b36f3394b85279f0585bdc`
- Source wave state recovered as `ACCEPTED / CHECKPOINTED`.
- Completion-report ACK gate was cleared authoritatively: subsequent governed `exec_command` admission succeeded.
- Accepted utility source surface is clean at delivery: `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py` and `resources/coding-tools-mcp/tests/test_orchestration_ledger.py` have no local modifications.

## Runtime/source activation boundary

- Utility/source commit: `d752d5b91700d47c6ca97e9d34eaba598a4f4ec6`.
- Current pre-closure HEAD observed: `73d0463b0d51cea4d81b62c5bf71a55ed3dedb86`.
- Controlled runtime restart evidence: `.coding-tools/orchestration/reports/runtime-restarts/runtime-restart-mcp-only-2026-08-22T06-59-57-328Z.json`.
- Restart completed at `2026-08-22T06:59:57.328Z`, after both commits above; MCP became ready and native PID changed `45328 -> 10688`.
- A separate P5 epoch `p5-6e995b1e3242412e9cc907e71c9f19c5` is owned by `codex-desktop`. It had zero active commands, lanes, managed processes, background operations and foreign heavy processes during restart preflight, but no standard EOCL context. The closure preserved that authority state rather than terminating or taking it over.

## Live ledger maintenance

Evidence report: `.coding-tools/orchestration/reports/maintenance/proof-metadata-migration-20260822T074621Z.json`.

- Canonical ledger: `.coding-tools/orchestration/ledger.sqlite3`.
- Journal mode before maintenance: `wal`.
- WAL-safe online backup was taken while `BEGIN IMMEDIATE` blocked concurrent writers.
- Backup path: `C:\Users\Admin\AppData\Local\Temp\coding-tools-mcp\b170d09bfa7bee20\iQx6C-rdAX3qOmzc\tmp\Codex-web-ledger-backups\ledger-pre-proof-metadata-20260822T074621Z.sqlite3`.
- Backup SHA-256: `fe8e886991745c460ae3603d08607f780d4d74b53f12f97e90e33f1251547e60`.
- Backup size: `85,704,704` bytes.
- Proof rows: `1,602` total; `120` BLOB and `1,482` TEXT before maintenance.
- Rows requiring migration under the accepted `_encode_proof_metadata` policy: `0`.
- Reason: all currently compression-beneficial proof metadata was already stored in the accepted `WCPM1\0 + zlib` representation; remaining legacy TEXT rows do not qualify for beneficial compression.
- `PRAGMA quick_check`: `ok` before and after.
- Table counts: unchanged inside the maintenance transaction.
- Logical proof SHA-256: unchanged at `881c78ba70df82eb4a12a09166a610cfeaceebe9805fd15ba0f61ad8e1ed502b`.
- `events.payload_json` SHA-256: unchanged at `00605a9e656417c84c8f8f8f0ebc9b05cb9e30dbf9dcd257953e26a7fa3124d3`.
- `idempotency_records.summary_json` SHA-256: unchanged at `5bc40d5d90939897daf2848cc1ab3512f28efa403de895bf30759e66744d7688`.
- `freelist_count`: `7,132`, so conditional `VACUUM` was eligible and completed successfully.
- Temporary operational helper was deleted before delivery and is not part of repository state.

## Regression / release gates

- Focused proof-metadata regression: `3 passed, 35 deselected`, exit `0`.
- Full MCP/Python suite: `521 passed, 3 skipped, 38 subtests passed`, exit `0`.
- Node suite: `251 passed, 0 failed`; source-root-clean check passed.
- Windows unpacked build: `npm run dist:dir`, exit `0`.
- Packaged recovery smoke: `ok=true`; executable/app.asar/resources valid; isolated userData; Recovery Host ready; MCP alive; supervisor healthy; live-owner and hash-mismatch fail-closed checks passed; no scheduled-task mutation.

## Delivery invariant

The delivery commit containing this receipt must include the complete required `.coding-tools` evidence snapshot while excluding the fixed transient sidecars `.coding-tools/orchestration/ledger.sqlite3-shm` and `.coding-tools/orchestration/ledger.sqlite3-wal`. The repository history and delivery guards must pass immediately before commit/push. The commit SHA is intentionally not embedded here because this file is itself part of that commit; Git history is the canonical delivery identity.
