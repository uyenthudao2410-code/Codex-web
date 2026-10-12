# r12 exact native no-effect observations

Root executes the supported read-only identity/census wrapper:

```text
node E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r12\reconciliation\root-native-no-effect-census.cjs --execute-read-only
```

The wrapper creates a new exclusive `native-no-effect-<observed_at_ms>.json`
receipt in this directory. It performs no replay, receipt terminalization,
acceptance, service change or canonical ledger mutation. Root owns execution.

The local collector reads the exact nested journal receipt, exact failed native
performance row, unchanged canary preimage/checker, zero new native ledger rows
since 19:49Z, and protected historical RUN/WAVE hashes in a read-only transaction.
The wrapper repeats the local observation around supported native identity reads,
the existing canonical ledger census and independent Sandbox/backend process
counts. All fields required by the server reconciliation packet are top-level.

`pre_effect=true` is derived from the unique native validation failure before RUN
creation, the exact unchanged target, and zero durable execution effects.
`performance_evidence_sha256` identifies the exact performance row; the separate
`performance_snapshot_sha256` identifies the volatile projection captured then.

`zero_vm=true` has the explicit basis
`no_matching_windows_sandbox_host_or_wxc_backend_processes`: the same bounded
Get-Process/CIM observation used by the pinned r12 transition. It does not assert
physical HCS inventory is empty. HCS list required higher privileges in the root
read-only probe, so `physical_hcs_inventory_claimed=false` stays explicit.

Preparation proof: Python AST, Node syntax and scoped whitespace passed. The
child executed only the local read-only collector and saved the preliminary
`local-no-effect-1791748822667.json` receipt. That preliminary receipt explicitly
requires the active census and is not the final combined proof.

This evidence supports reconciliation of only action
`act_6aa1329b96c146f38c807f9926b3e684`, task
`task_d2c1dd3bff4042d084b045e9bc5a381b`, attempt
`try_4178cd41d2f3424a81dcb3c4cc706ed1`. It grants no new authority or retry.
