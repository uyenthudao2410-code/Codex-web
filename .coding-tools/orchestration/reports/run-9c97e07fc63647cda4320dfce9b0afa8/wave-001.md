# Orchestration Wave 1

- Run: `9c97e07fc63647cda4320dfce9b0afa8`
- Wave: `ae8ace7f814c4cd08159be383df9da4b`
- Objective: Fix only case.py so normalize_score clamps values below 0 to 0, values above 100 to 100, and leaves values in [0,100] unchanged. Do not modify test_case.py. The deterministic acceptance oracle is `python test_case.py`. This is a paired benchmark fixture, not production source.
- Mode: `bounded_candidate`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `3e8a971444c01f8c07ef0d2840447e37189346c5595103d2676a69b5f872fb23`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 646ed9ae5d844c3d97c99689900d4940 | CODEX:mini | mini | mini | gpt-5.4-mini | low | accepted_candidate |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1240 | 2026-08-14T06:06:27.451Z | run_started |  | PREFLIGHT |  |
| 1241 | 2026-08-14T06:06:28.024Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1242 | 2026-08-14T06:06:28.292Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 1243 | 2026-08-14T06:06:28.467Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1244 | 2026-08-14T06:06:28.642Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1245 | 2026-08-14T06:06:28.810Z | route_selected | READY | READY | reason=explicit_request; requested=mini; resolved=mini |
| 1246 | 2026-08-14T06:06:28.967Z | state_transition | READY | ROUTED | reason=route_selected |
| 1247 | 2026-08-14T06:06:29.293Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:mini |
| 1248 | 2026-08-14T06:06:29.478Z | model_dispatch_started | ROUTED | ROUTED |  |
| 1249 | 2026-08-14T06:06:38.020Z | model_dispatch_finished | ROUTED | ROUTED | status=completed |
| 1250 | 2026-08-14T06:06:38.276Z | delegation_finished | ROUTED | ROUTED | status=accepted_candidate |
| 1251 | 2026-08-14T06:06:38.792Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=96b5f7c3b21545beb245db95901d6ae4 |
| 1252 | 2026-08-14T06:06:38.960Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1253 | 2026-08-14T06:06:39.637Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=96b5f7c3b21545beb245db95901d6ae4 |
| 1254 | 2026-08-14T06:06:39.793Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1255 | 2026-08-14T06:06:40.414Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3d05bdfdc8b397dfb6f84839c679ec2675ed5404744473a7e81560671fcdae56 |
| 1256 | 2026-08-14T06:06:40.677Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1257 | 2026-08-14T06:06:53.142Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 3d05bdfdc8b397dfb6f84839c679ec2675ed5404744473a7e81560671fcdae56 | False | 109 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ffa898172aed476380b73768e67e4e2a | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | cfbf18e813c33c12f4170f2249b868e47f58639efa1094f3a325f7325da4c6e5 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `52ccc3408fa7c9b8fe204afd3ceef6cff9c0564f0bb6e35b7bd49e974cbeebc0`
