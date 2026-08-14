# Orchestration Wave 1

- Run: `7b8dd6b518934c78b26946821c3ac6ef`
- Wave: `58217a09b34c422d846e267de06ac911`
- Objective: Create two additional paired localized strong-oracle benchmark cases for Mini/Luna under tmp/execution-hub-benchmark. Case capacity tests non-negative remaining-capacity arithmetic; case timeout tests default/fallback semantics. Each route copy is identical and isolated. Benchmark setup only; do not touch production source.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `e9ba28712186cae6a0a6a4722118ac4bc2ffb7fd69b873da4d7b25aabe09ea5f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1290 | 2026-08-14T06:14:20.479Z | run_started |  | PREFLIGHT |  |
| 1291 | 2026-08-14T06:14:20.981Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1292 | 2026-08-14T06:14:21.128Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1293 | 2026-08-14T06:14:21.332Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1294 | 2026-08-14T06:14:21.543Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1295 | 2026-08-14T06:14:21.731Z | state_transition | READY | ROUTED | reason=route_selected |
| 1296 | 2026-08-14T06:14:22.311Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0a85b143260c40119d1241fe22f915eb |
| 1297 | 2026-08-14T06:14:22.500Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1298 | 2026-08-14T06:14:23.570Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0a85b143260c40119d1241fe22f915eb |
| 1299 | 2026-08-14T06:14:23.806Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1300 | 2026-08-14T06:14:24.461Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1301 | 2026-08-14T06:14:37.332Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 8ea3ba34f4654d8a85840acfd421d074 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `0ed73215a30e7c0564d1a9bf5cda890d0dfe20c5b25c9c9fb6f39efbf780e69d`
