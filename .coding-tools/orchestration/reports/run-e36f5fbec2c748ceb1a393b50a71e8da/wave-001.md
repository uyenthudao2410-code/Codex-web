# Orchestration Wave 1

- Run: `e36f5fbec2c748ceb1a393b50a71e8da`
- Wave: `6bfd59996efe45528a0f0c20a818e9a7`
- Objective: Run one broad Python MCP regression on the exact current P0 worktree because the changes cross public tool schema, orchestration ledger evaluation, promotion readiness, and paired economics. Proof-only; do not mutate source.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `5993fbd75d3810d46e0f228a924a89a6d7e3a2059518f4f8362fa84fff8ba2cf`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4822 | 2026-08-15T07:48:46.304Z | run_started |  | PREFLIGHT |  |
| 4823 | 2026-08-15T07:48:46.905Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4824 | 2026-08-15T07:50:47.168Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 4825 | 2026-08-15T07:50:47.321Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4826 | 2026-08-15T07:50:47.532Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4827 | 2026-08-15T07:50:47.744Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4828 | 2026-08-15T07:50:47.959Z | state_transition | READY | ROUTED | reason=route_selected |
| 4829 | 2026-08-15T07:50:48.514Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c73cd578191547249e48a0c60117eb8b |
| 4830 | 2026-08-15T07:50:48.695Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4831 | 2026-08-15T07:50:49.319Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c73cd578191547249e48a0c60117eb8b |
| 4832 | 2026-08-15T07:50:49.500Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4833 | 2026-08-15T07:50:49.979Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b4434c1067e09fd57c0536a7d437a1889da6ab376673e3582c149eb8802dc5ae |
| 4834 | 2026-08-15T07:52:47.565Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b4434c1067e09fd57c0536a7d437a1889da6ab376673e3582c149eb8802dc5ae |
| 4835 | 2026-08-15T07:52:48.393Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4836 | 2026-08-15T07:53:04.294Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | b4434c1067e09fd57c0536a7d437a1889da6ab376673e3582c149eb8802dc5ae | False | 117000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ee7c61ec72ba4ed59271c960bc6f64d1 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | fed807a60bd5d01a3ed78bd48852f4f313996b788d68e98bc0ab721c75c776e2 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `471b72e1d054b53460e3e502f4e7b601e8678939ac6e9052775ca22e684d99f5`
