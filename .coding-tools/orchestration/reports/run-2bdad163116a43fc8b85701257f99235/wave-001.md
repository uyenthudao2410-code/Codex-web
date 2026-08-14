# Orchestration Wave 1

- Run: `2bdad163116a43fc8b85701257f99235`
- Wave: `e8d7104c64ec411890473fc2a34e658f`
- Objective: Fix only case.py so normalize_score clamps values below 0 to 0, values above 100 to 100, and leaves values in [0,100] unchanged. Do not modify test_case.py. The deterministic acceptance oracle is `python test_case.py`. This is the Luna paired benchmark fixture, not production source.
- Mode: `bounded_candidate`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `3e8a971444c01f8c07ef0d2840447e37189346c5595103d2676a69b5f872fb23`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 1214e8cfa0664f4a8e3da351688daba0 | CODEX:luna | luna | luna | gpt-5.6-luna | high | accepted_candidate |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1258 | 2026-08-14T06:07:02.017Z | run_started |  | PREFLIGHT |  |
| 1259 | 2026-08-14T06:07:02.547Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1260 | 2026-08-14T06:07:02.842Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 1261 | 2026-08-14T06:07:03.008Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1262 | 2026-08-14T06:07:03.233Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1263 | 2026-08-14T06:07:03.424Z | route_selected | READY | READY | reason=explicit_request; requested=luna; resolved=luna |
| 1264 | 2026-08-14T06:07:03.620Z | state_transition | READY | ROUTED | reason=route_selected |
| 1265 | 2026-08-14T06:07:03.963Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:luna |
| 1266 | 2026-08-14T06:07:04.190Z | model_dispatch_started | ROUTED | ROUTED |  |
| 1267 | 2026-08-14T06:07:13.096Z | model_dispatch_finished | ROUTED | ROUTED | status=completed |
| 1268 | 2026-08-14T06:07:13.374Z | delegation_finished | ROUTED | ROUTED | status=accepted_candidate |
| 1269 | 2026-08-14T06:07:13.977Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0d18ecbb8bd5427582119ceea150bb32 |
| 1270 | 2026-08-14T06:07:14.170Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1271 | 2026-08-14T06:07:14.850Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0d18ecbb8bd5427582119ceea150bb32 |
| 1272 | 2026-08-14T06:07:15.025Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1273 | 2026-08-14T06:07:15.875Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3a46f5a374acc0a3f9103fe36506e0c1d65fe9a6ce0ebcecec10382cf7a2e287 |
| 1274 | 2026-08-14T06:07:16.184Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1275 | 2026-08-14T06:07:28.666Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 3a46f5a374acc0a3f9103fe36506e0c1d65fe9a6ce0ebcecec10382cf7a2e287 | False | 109 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c8ed894d16ea4011a4a16211c58f0dfa | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 699938d7725b9355b6c39bdb065a24400b94338de0c06a62c1a02582f6441c34 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `11b65f813662cec9b1c7f62d2d60d090520fd3ec181a849ae9331c4a3ceaef6d`
