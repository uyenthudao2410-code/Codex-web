# Orchestration Wave 1

- Run: `500cfd73fde5464c862c84206887e09f`
- Wave: `ea1720485d7d4ff99f66097361e37b96`
- Objective: Capture a fresh runtime-activation/cohort-v2 snapshot after the completed P1.5 activation and candidate-packet hardening. Run only the canonical benchmark command, do not modify source, do not change routing thresholds, and report accepted-route cohort coverage including whether any representative accepted Mini/Luna/Sol samples now exist.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `26adece75d943ced8abedcd3dbc4a369fbb0af0adc1de1cc71aa1520449acd83`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 869 | 2026-08-14T04:14:20.167Z | run_started |  | PREFLIGHT |  |
| 870 | 2026-08-14T04:14:20.665Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 871 | 2026-08-14T04:14:20.840Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 872 | 2026-08-14T04:14:20.981Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 873 | 2026-08-14T04:14:21.155Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 874 | 2026-08-14T04:14:21.323Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 875 | 2026-08-14T04:14:21.501Z | state_transition | READY | ROUTED | reason=route_selected |
| 876 | 2026-08-14T04:14:22.064Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=860848eee57745e0924332cf7a5ce252 |
| 877 | 2026-08-14T04:14:22.260Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 878 | 2026-08-14T04:14:22.842Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=860848eee57745e0924332cf7a5ce252 |
| 879 | 2026-08-14T04:14:23.026Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 880 | 2026-08-14T04:14:24.881Z | proof_recorded |  |  | stage_id=check:d97ff2ecbaa79b27; status=passed; cache_hit=False; input_fingerprint=3299686fd5dd009baf285f42c2977247d89bce90fecbb8d78e0ea7715e30a95f |
| 881 | 2026-08-14T04:14:25.058Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 882 | 2026-08-14T04:14:51.552Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d97ff2ecbaa79b27 | passed | 3299686fd5dd009baf285f42c2977247d89bce90fecbb8d78e0ea7715e30a95f | False | 1254 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 106a987d272549fb9383e60e60214026 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | acbadc37d971a81c9ba2ae2f8e07fd863006b678f5ef56cf949cd9fdb81c5fd2 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `dc1707d7bad6e8d414fddf609dcf67cb422f36353fafd973cdc196ce748146ce`
