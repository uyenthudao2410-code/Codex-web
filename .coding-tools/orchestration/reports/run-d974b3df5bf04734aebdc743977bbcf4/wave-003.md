# Orchestration Wave 3

- Run: `d974b3df5bf04734aebdc743977bbcf4`
- Wave: `4f75b43ae4ee4b3295527b7deec26672`
- Objective: Fix only case.py so remaining_capacity(limit, used) returns the non-negative remaining capacity: limit-used when positive, otherwise 0. Do not modify test_case.py. Deterministic oracle: `python test_case.py`. Localized strong-oracle benchmark only.
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
| 1333 | 2026-08-14T06:15:59.066Z | wave_replanned |  | PREFLIGHT | reason=The second Mini wave successfully applied the intended patch, but verification executed from repository root despite a subdirectory workdir and therefore could not find `test_case.py`. Preserve the applied patch and switch to deterministic proof-only with an explicit workspace-relative test path; no further model call is justified. |
| 1334 | 2026-08-14T06:15:59.253Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1335 | 2026-08-14T06:15:59.433Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1336 | 2026-08-14T06:15:59.652Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 1337 | 2026-08-14T06:15:59.835Z | state_transition | READY | ROUTED | reason=route_selected |
| 1338 | 2026-08-14T06:16:00.453Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=db05e1f4030546478ef76f923af33755 |
| 1339 | 2026-08-14T06:16:00.625Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1340 | 2026-08-14T06:16:01.277Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=db05e1f4030546478ef76f923af33755 |
| 1341 | 2026-08-14T06:16:01.479Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1342 | 2026-08-14T06:16:02.258Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3a3b5dfed6c27803413d89319911c542a6f574990e0894a26653497237789074 |
| 1343 | 2026-08-14T06:16:02.459Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1344 | 2026-08-14T06:16:20.972Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 3a3b5dfed6c27803413d89319911c542a6f574990e0894a26653497237789074 | False | 125 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| df1838623d0c4a8c8e2df2c2f58ae644 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | ae565948a7cd0ea72eb709ac0852546b56c006cdabfe03d87e4859dda660b812 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `43`
- Chain head: `374e9bd8bd7434cc08e34611d4632ce00084eb2bb0dc53d6c9bb0032fef0122c`
