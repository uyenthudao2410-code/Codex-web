# Orchestration Wave 1

- Run: `11ddc1dafef442f6a54c83a44568eb3a`
- Wave: `debf7d6fb8c24fee9c88656d85d355a8`
- Objective: Fix only `tmp/execution-hub-benchmark/capacity-luna/case.py` so remaining_capacity(limit, used) returns limit-used when positive and 0 otherwise. Do not modify `tmp/execution-hub-benchmark/capacity-luna/test_case.py`. Deterministic oracle: `python tmp/execution-hub-benchmark/capacity-luna/test_case.py`. Localized strong-oracle Luna benchmark only.
- Mode: `bounded_candidate`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `e9ba28712186cae6a0a6a4722118ac4bc2ffb7fd69b873da4d7b25aabe09ea5f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 75270c3ce8eb44bbbd9accf05a353e0b | CODEX:luna | luna | luna | gpt-5.6-luna | high | accepted_candidate |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1345 | 2026-08-14T06:16:33.501Z | run_started |  | PREFLIGHT |  |
| 1346 | 2026-08-14T06:16:33.951Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1347 | 2026-08-14T06:16:34.237Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 1348 | 2026-08-14T06:16:34.457Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1349 | 2026-08-14T06:16:34.610Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1350 | 2026-08-14T06:16:34.808Z | route_selected | READY | READY | reason=explicit_request; requested=luna; resolved=luna |
| 1351 | 2026-08-14T06:16:35.012Z | state_transition | READY | ROUTED | reason=route_selected |
| 1352 | 2026-08-14T06:16:35.342Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:luna |
| 1353 | 2026-08-14T06:16:35.601Z | model_dispatch_started | ROUTED | ROUTED |  |
| 1354 | 2026-08-14T06:16:40.832Z | model_dispatch_finished | ROUTED | ROUTED | status=completed |
| 1355 | 2026-08-14T06:16:41.136Z | delegation_finished | ROUTED | ROUTED | status=accepted_candidate |
| 1356 | 2026-08-14T06:16:41.723Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=045dd90ed189410eadf88070429d377d |
| 1357 | 2026-08-14T06:16:41.897Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1358 | 2026-08-14T06:16:42.540Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=045dd90ed189410eadf88070429d377d |
| 1359 | 2026-08-14T06:16:42.801Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1360 | 2026-08-14T06:16:43.564Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=04540ee0c4182e62da9fb0201cb75e0d51e1a3e037c9b8e039753333d1772282 |
| 1361 | 2026-08-14T06:16:43.907Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1362 | 2026-08-14T06:18:10.814Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 04540ee0c4182e62da9fb0201cb75e0d51e1a3e037c9b8e039753333d1772282 | False | 125 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6cc20619421045149680bec4e83cf7c0 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | ddc3954651232499ed78ce4be76b296c2b4e785fa2b4ff05a525a7fe6dc4b0eb | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `3d676b0847a2b308ab0bdab0062f252e6b2bd823e70d53488623835a8c2901c2`
