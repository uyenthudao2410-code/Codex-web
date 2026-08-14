# Orchestration Wave 1

- Run: `82d3a99b3aac4ae3a76219c0d33a6a2d`
- Wave: `363f17b91f4b43669ad590a567dd9a4c`
- Objective: Finish dashboard truthfulness copy for the retained recent trace window. Do not change layout or analytics math. Replace full-day/billing-sounding labels with recent-trace context/evidence labels: model-visible bytes are MEASURED, byte-to-token is ESTIMATED, model usage is MEASURED only when delegation economics supplies numeric counters, and all configured-rate costs are SCENARIO rather than provider billing.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `11a378e143315e1d007893f073217b85d0d24652fefb889ea3ea885f4942b2f3`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1656 | 2026-08-14T08:48:24.479Z | run_started |  | PREFLIGHT |  |
| 1657 | 2026-08-14T08:48:24.989Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1658 | 2026-08-14T08:48:25.158Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1659 | 2026-08-14T08:48:25.334Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1660 | 2026-08-14T08:48:25.491Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1661 | 2026-08-14T08:48:25.684Z | state_transition | READY | ROUTED | reason=route_selected |
| 1662 | 2026-08-14T08:48:26.279Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bf46b271b35643bdaa8817b7fbe3ba00 |
| 1663 | 2026-08-14T08:48:26.456Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1664 | 2026-08-14T08:48:27.153Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bf46b271b35643bdaa8817b7fbe3ba00 |
| 1665 | 2026-08-14T08:48:27.324Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1666 | 2026-08-14T08:48:28.269Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=c346f46e0538563616b79a1c11c27d46ebfd5843e8a0edfe7fa083aa9f5456e3 |
| 1667 | 2026-08-14T08:48:37.380Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1668 | 2026-08-14T08:48:47.574Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | c346f46e0538563616b79a1c11c27d46ebfd5843e8a0edfe7fa083aa9f5456e3 | False | 296 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 2f6c808954654faba2685e2e3cef58e4 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | cc145f6720a1b9f0e0f3ebbde4cc8c139ebb71a961b3f4dd59f25990d3700d50 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `50aece2f44c8b51cf0e9603205a79bdc7f2b00d9632ece60a496281ffa490f2d`
