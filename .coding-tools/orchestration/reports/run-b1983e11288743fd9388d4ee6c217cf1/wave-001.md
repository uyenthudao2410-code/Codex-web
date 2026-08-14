# Orchestration Wave 1

- Run: `b1983e11288743fd9388d4ee6c217cf1`
- Wave: `13798c9334244131af9dd8bd2798fae4`
- Objective: Fix the live universal-idempotency duplicate replay delivery bug demonstrated through the refreshed connector. Preserve durable ledger redaction and all routing/high-cost/security policy. On completed universal replay, do not return the sanitized stored MCP envelope verbatim because ledger sanitization turns top-level content into a non-list; rebuild a fresh valid MCP tool result from the stored structuredContent plus deduplicated/durable idempotency metadata. Preserve isError. Add a focused regression assertion that a duplicate exec_command replay returns MCP content as a list while retaining dedup flags and one-side-effect semantics. Do not touch agent_workflow's separate idempotency path or unrelated files.
- Mode: `mcp_only`
- Base HEAD: `8deb55e72fc6a8af6ae801555e65825cb46ceff4`
- Worktree fingerprint: `6acef19b220e97e44ff72cfcaafaea99dc38a9ca6c25ab1bde93e1a7791cb589`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 574 | 2026-08-14T00:05:16.158Z | run_started |  | PREFLIGHT |  |
| 575 | 2026-08-14T00:05:16.501Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 576 | 2026-08-14T00:05:16.625Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 577 | 2026-08-14T00:05:16.727Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 578 | 2026-08-14T00:05:16.841Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 579 | 2026-08-14T00:05:16.938Z | state_transition | READY | ROUTED | reason=route_selected |
| 580 | 2026-08-14T00:05:17.384Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8e7c62ebabfa4138ba3a84395bb517e2 |
| 581 | 2026-08-14T00:05:17.508Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 582 | 2026-08-14T00:05:17.908Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8e7c62ebabfa4138ba3a84395bb517e2 |
| 583 | 2026-08-14T00:05:18.027Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 584 | 2026-08-14T00:05:22.471Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=8403b45b0c5cb3b6c1ecffc4e933f765c1460e09350a75b49cf20a4853e97eea |
| 585 | 2026-08-14T00:05:22.686Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 586 | 2026-08-14T00:05:34.574Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 8403b45b0c5cb3b6c1ecffc4e933f765c1460e09350a75b49cf20a4853e97eea | False | 4094 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 25e51f447ecc4dc8bdbb2ff1a2cda0f9 | accepted | 8deb55e72fc6a8af6ae801555e65825cb46ceff4 | cb9ffeaa52c439ea6061801db8fc66e11983a1ac2706d3614f170755562ba4f2 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `d53805982436fbb243fa4b81c550d1fa9fd6122ee08b97dfd7c1b2422a5713d1`
