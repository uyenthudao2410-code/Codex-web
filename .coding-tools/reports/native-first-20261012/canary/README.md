# Native first live canary — prepared, not executed

This harness uses the existing authenticated Ubuntu MCP facade and the enrolled
Windows node. It requires a fresh, exact Codex-web scoped pilot, packaged READY
runtime identity, facade digest, service PID and serving source hashes.

## Operations

- Separate local preparation creates 100 tiny seed files and a bounded Node
  build script under `tests/fixtures/native-first-canary`. Existing targets are
  refused. Local preparation is not a shared MCP creation proof.
- One durable MCP task and writer lease authorize 100 reads, 20 exact patches,
  20 exact readbacks, 10 unique `node --version` Jobs and Git status/diff/log.
  The base run dispatches 153 actions.
- Optional explicitly approved `node trusted-build.js` validates the same 100
  files and creates one exclusive artifact. An additional MCP read verifies it.
  The optional run dispatches 155 actions.
- Every action must have exactly one delivery attempt and a verified receipt
  matching runtime, facade and task lineage. Every exec receipt/status/output
  must attest native/process_container and the expected policy decision.
- Windows Sandbox/vmmem process counts and memory are sampled before/after.
  Two samples cannot exclude a transient VM; routing receipts prove the backend.

## Readiness pins

Supply a reviewed JSON file with `activation_verified: true`,
`workspace_label: "Codex-web"`, `principal_id`, `grant_id`, `device_id`,
`workspace_id`, `binding_id`, `workspace_generation`, `pilot_decision_id`,
`activation_epoch`, `process_instance_id`, `server_instance_id`,
`local_tool_contract_sha256`, `facade_schema_version`,
`facade_contract_sha256`, `serving_mcp_facade_sha256`,
`serving_node_agent_sha256`, and `service_pid`. The optional build also requires
`trusted_build_explicitly_approved: true` and the existing local policy approval
for argv `["node", "trusted-build.js"]` with the exact fixture cwd.
No credential belongs in this file.

## Safety and closure

Credentials and service environment remain Ubuntu-side in memory. SQLite is
opened read-only. Output contains safe evidence projections, hashes and handles;
raw source, Git output, errors and credential bytes are not emitted.

Each lane is single use. A lost response recovers only its original action from
durable idempotency state. No replacement action is dispatched. On failure the
harness observes original actions, and stops only its own unsettled execs when
their effect is known. It releases its writer and closes its task only when all
original actions are settled and none requires reconciliation. SQLite then
verifies `closed_at_ms` and no unreleased lease. Unknown actions retain their
task boundary and are reported for reconciliation.

Current blocker: three historical Autocad read actions are UNKNOWN. Existing
owner Console and MCP paths also use the global scoped-pilot admission guard;
they cannot independently admit Codex-web while preserving the Autocad pilot.
This harness does not modify or classify those actions.

Plan-only fixture command: `python -B prepare-native-first-fixtures.py`.
Actual preparation requires `--prepare-fixtures`. Actual SSH execution requires
the explicit wrapper switch and reviewed fresh pins. Neither has been executed
as part of preparing this harness.
