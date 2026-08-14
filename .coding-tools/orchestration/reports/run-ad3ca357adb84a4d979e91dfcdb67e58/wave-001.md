# Orchestration Wave 1

- Run: `ad3ca357adb84a4d979e91dfcdb67e58`
- Wave: `993ed6e5789f494f9826be3f21a89013`
- Objective: Fix only `tmp/execution-hub-benchmark/timeout-luna/case.py` so select_timeout(value, default=30) returns default when value is None or value <= 0, and returns positive values unchanged. Do not modify `tmp/execution-hub-benchmark/timeout-luna/test_case.py`. Deterministic oracle: `python tmp/execution-hub-benchmark/timeout-luna/test_case.py`. Localized strong-oracle Luna benchmark only.
- Mode: `bounded_candidate`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `e9ba28712186cae6a0a6a4722118ac4bc2ffb7fd69b873da4d7b25aabe09ea5f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| e025fd35bde74853857fd2490c239e2e | CODEX:luna | luna | luna | gpt-5.6-luna | high | accepted_candidate |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1381 | 2026-08-14T06:18:55.176Z | run_started |  | PREFLIGHT |  |
| 1382 | 2026-08-14T06:18:55.686Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1383 | 2026-08-14T06:18:56.034Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 1384 | 2026-08-14T06:18:56.272Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1385 | 2026-08-14T06:18:56.437Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1386 | 2026-08-14T06:18:56.663Z | route_selected | READY | READY | reason=explicit_request; requested=luna; resolved=luna |
| 1387 | 2026-08-14T06:18:56.862Z | state_transition | READY | ROUTED | reason=route_selected |
| 1388 | 2026-08-14T06:18:57.236Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:luna |
| 1389 | 2026-08-14T06:18:57.464Z | model_dispatch_started | ROUTED | ROUTED |  |
| 1390 | 2026-08-14T06:19:05.036Z | model_dispatch_finished | ROUTED | ROUTED | status=completed |
| 1391 | 2026-08-14T06:19:05.336Z | delegation_finished | ROUTED | ROUTED | status=accepted_candidate |
| 1392 | 2026-08-14T06:19:05.961Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0d5ba8104eb34f3b89c6666bc7386b1e |
| 1393 | 2026-08-14T06:19:06.192Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1394 | 2026-08-14T06:19:06.877Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0d5ba8104eb34f3b89c6666bc7386b1e |
| 1395 | 2026-08-14T06:19:07.100Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1396 | 2026-08-14T06:19:07.951Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ada7382687d1ed91ed42803d57cdb192a362ce166f005f734bb1c25c675c06db |
| 1397 | 2026-08-14T06:19:08.327Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1398 | 2026-08-14T06:19:25.469Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | ada7382687d1ed91ed42803d57cdb192a362ce166f005f734bb1c25c675c06db | False | 110 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 3ba41d122c634a2db06c49b4506b8759 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 2d75321887810843c5e9bbfa8d198a275f9cd14ccf51791bb17f4fcfc1dc429c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `a391289bf3db0630598bb19121399419b35c847e8e0d45dbbf40ae518cda0f9e`
