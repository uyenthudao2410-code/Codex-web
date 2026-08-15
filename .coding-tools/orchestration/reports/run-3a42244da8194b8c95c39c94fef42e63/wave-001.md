# Orchestration Wave 1

- Run: `3a42244da8194b8c95c39c94fef42e63`
- Wave: `9ba8189ac44548d4a43b4b5ec0c0389b`
- Objective: Targeted follow-up: surface only the non-secret current auth-email match, consolidated Codex model/provider/base_url, and listener owner for port 4102. No mutation or restart.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `a152d14a82d064b843730022b3b9c420e297511f6e68f63b393b38ea5ce41590`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4720 | 2026-08-15T07:42:07.772Z | run_started |  | PREFLIGHT |  |
| 4721 | 2026-08-15T07:42:08.461Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4722 | 2026-08-15T07:42:08.812Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 4723 | 2026-08-15T07:42:09.190Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4724 | 2026-08-15T07:42:09.561Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4725 | 2026-08-15T07:42:09.796Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4726 | 2026-08-15T07:42:10.139Z | state_transition | READY | ROUTED | reason=route_selected |
| 4727 | 2026-08-15T07:42:10.770Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f898274d422e4801ad22fbd3aaa2e71f |
| 4728 | 2026-08-15T07:42:10.974Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4729 | 2026-08-15T07:42:11.574Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f898274d422e4801ad22fbd3aaa2e71f |
| 4730 | 2026-08-15T07:42:11.774Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4731 | 2026-08-15T07:42:12.293Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b6159d4a6f735add; input_fingerprint=8d7bc468511ac85e79b819c2eb9b48f260cea5e5e1dbff06df00c22cc4e0bdef |
| 4732 | 2026-08-15T07:42:18.317Z | proof_recorded |  |  | stage_id=check:b6159d4a6f735add; status=passed; cache_hit=False; input_fingerprint=8d7bc468511ac85e79b819c2eb9b48f260cea5e5e1dbff06df00c22cc4e0bdef |
| 4733 | 2026-08-15T07:42:18.515Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fd22eb65a8ea219e; input_fingerprint=5cfa27cf2b512819651826dc0fc44b9f676d1dc1475f06a54066780dbfe2527e |
| 4734 | 2026-08-15T07:42:19.648Z | proof_recorded |  |  | stage_id=check:fd22eb65a8ea219e; status=passed; cache_hit=False; input_fingerprint=5cfa27cf2b512819651826dc0fc44b9f676d1dc1475f06a54066780dbfe2527e |
| 4735 | 2026-08-15T07:42:19.868Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0bb47195eedfad6c; input_fingerprint=45413a0b370dce19b1db5bcf49d76a7b049c5a410aa4b04caa8750d3d2fb91b5 |
| 4736 | 2026-08-15T07:42:22.677Z | proof_recorded |  |  | stage_id=check:0bb47195eedfad6c; status=passed; cache_hit=False; input_fingerprint=45413a0b370dce19b1db5bcf49d76a7b049c5a410aa4b04caa8750d3d2fb91b5 |
| 4737 | 2026-08-15T07:42:23.023Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4738 | 2026-08-15T07:42:39.746Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b6159d4a6f735add | passed | 8d7bc468511ac85e79b819c2eb9b48f260cea5e5e1dbff06df00c22cc4e0bdef | False | 5679 | 0 |
| check:fd22eb65a8ea219e | passed | 5cfa27cf2b512819651826dc0fc44b9f676d1dc1475f06a54066780dbfe2527e | False | 712 | 0 |
| check:0bb47195eedfad6c | passed | 45413a0b370dce19b1db5bcf49d76a7b049c5a410aa4b04caa8750d3d2fb91b5 | False | 2246 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 9dc8297705294ba7a6756e201859d850 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | fba4ecb0f3a6c90f88efd1675e17de68328d2b3d9ec8b3f736f4d485cbc213be | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `c11e3c9c087d56fe50e07425eb02636f990c1968a6fa130442010f689970b473`
