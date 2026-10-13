# Two-root native overlap canary

Prepared locally on 2026-10-12. This preparation did not create target fixtures,
open a task, claim a writer lease, dispatch an action, restart a service or run SSH.
The separate Codex-web 100/20/10 canary uses the existing harness.

## Scope and proof

- Exactly two reviewed targets: `Codex-web` and `Autocad`, with distinct binding,
  workspace and pilot-decision identities, and each target's current generation.
- Same reviewed packaged Windows runtime identity and local/facade contract.
- Two tasks and their original writer leases remain held at the same time.
- Each root has a new `tests/fixtures/parallel-native-overlap-20261012` directory
  containing `probe.txt` and a root-specific `hold.cjs`. Local preparation is
  reported separately from remote FileAPI proof.
- Per root: one FileAPI read, one guarded exact patch, one readback, one native
  Node Job. Neither implementation nor build files in AutoCAD are touched.
- Exact native approval is `['node',
  'tests/fixtures/parallel-native-overlap-20261012/hold.cjs']`, with empty `cwd`.
  The reviewed policy digest and fixture source digest are pinned per root.
- The harness reads original `accepted` receipts from the central SQLite ledger
  in read-only mode, records both native running handles, then verifies each
  terminal receipt against the existing imported receipt checker.
- Each fixture holds for about five seconds and emits bounded PID and start/end
  timestamps. The final proof requires two distinct Jobs/commands/PIDs and a
  positive interval intersection on the same Windows node. A running receipt
  alone does not establish that a process remained alive at a later observation.
- After both accepted running handles, the central HTTP observation client is
  recreated with the same in-memory credential. Exact target/contract pins are
  rechecked, and completion is observed on the original actions and handles.
  This proves observation-client reconnect when live; it does not claim a
  Windows runtime restart or local semantic acceptance.
- UNKNOWN keeps its original action/task/lease open for reconciliation. A lost
  response is recovered by its original idempotency key and is never redispatched.
  One unresolved root does not prevent cleanup of the other root's settled work.
- Autocad may carry exactly three reviewed historical UNKNOWN action IDs in
  `retained_unknown_actions`. They must remain expired, unsettled bounded reads
  with no local handle and the canonical `quarantined_unknown` disposition and
  `HISTORICAL_READ_ONLY_UNKNOWN_EFFECT` declaration. The pinned serving Store's
  predicate verifies intent/action/receipt/quarantine digest lineage in read-only
  mode. Any other unsettled action blocks the canary. These historical handles
  are recorded separately and are never settled, stopped, replayed or cleaned up.
- Exact patch effect is proved; local semantic acceptance remains pending and is
  explicitly reported. No AutoCAD/.NET/Python production build is claimed.

## Prepare and execute

First run `prepare-parallel-overlap-fixtures.py` with `--codex-root` and
`--autocad-root` set to the two authorized registered repository roots. This
prints the plan and label-specific fixture hashes without writing fixtures.

After reviewing that plan, run the same command with `--prepare-fixtures` and
an absolute, new `--manifest-path` in this canary directory. The command refuses
existing fixture directories, existing receipts, aliased roots and reparse
ancestors. It adds exactly two files per root and retains them as canary evidence.

Fresh reviewed pins JSON has `schema_version: 1`, common fields
`principal_id`, `grant_id`, `device_id`, `activation_epoch`, `process_instance_id`,
`server_instance_id`, `service_pid`, `facade_schema_version`,
`local_tool_contract_sha256`, `facade_contract_sha256`,
`serving_mcp_facade_sha256`, `serving_node_agent_sha256` and `serving_store_sha256`.

Its `targets` array contains one object per label with `workspace_label`,
`workspace_id`, `workspace_generation`, `binding_id`, `pilot_decision_id`,
`activation_verified: true`, `native_fixture_explicitly_approved: true`,
`native_argv`, `native_cwd`, `native_source_sha256` and `exec_policy_sha256`.
Only the Autocad object may add exactly three reviewed `retained_unknown_actions`;
omission means no historical allowance. Codex-web must have no unsettled actions.
The fixture manifest supplies the exact native argv/cwd/source digest values.
The credential remains at its protected Ubuntu service path and is never
included in pins, source, receipts or command output.

Execute `invoke-parallel-overlap-canary.ps1` with
`-ExecuteConfirmedReadyTwoRootCanary`, `-ReadyPinsPath`, `-FixtureManifestPath`
and a new GUID `-AttemptId`. These explicit switches guard the reviewed target
and one-use attempt; they do not request a new user authorization. The wrapper
checks seed hashes, source hashes and both Git HEADs, then streams the imported
module, runner and reviewed pins through SSH in memory. No remote source file
or credential copy is created. A receipt path cannot be overwritten or reused.

The before/after Windows Sandbox process census is a bounded observation.
It cannot exclude transient VM startup. Exact native receipts establish the
execution backend; fixture intervals establish overlap.

## Offline checks

`python -B test-parallel-overlap-canary.py`: five tests passed. They cover exact
per-root source approvals, distinct scopes, interval intersection, lost-response
recovery, UNKNOWN preservation, exact quarantined-history preflight and independent cleanup. PowerShell parser
validation passed. These checks do not prove a live overlap or production build.
