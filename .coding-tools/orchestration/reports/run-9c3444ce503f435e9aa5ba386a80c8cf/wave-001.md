# Orchestration Wave 1

- Run: `9c3444ce503f435e9aa5ba386a80c8cf`
- Wave: `b0dea52581524f2994b0bcef31e26182`
- Objective: Wave B2: accepted_result_economics dùng run_phase_timing làm nguồn TTA coverage duy nhất, thêm provider timing delegation metadata dưới evidence overlapping, và bổ sung deterministic tests cho coverage gate + provider timing. Không cộng provider timing vào EOCL observed_ms.
- Mode: `mcp_only`
- Base HEAD: `62ff046711503260b079e53a85c66e5b9af01e32`
- Worktree fingerprint: `c6f9c29aac65b5604da2667d9d9ddd0fa90d14e938886bd51fce12590ad2f748`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2750 | 2026-08-14T16:18:45.158Z | run_started |  | PREFLIGHT |  |
| 2751 | 2026-08-14T16:18:45.329Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2752 | 2026-08-14T16:18:45.454Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2753 | 2026-08-14T16:18:45.609Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2754 | 2026-08-14T16:18:45.749Z | state_transition | READY | ROUTED | reason=route_selected |
| 2755 | 2026-08-14T16:18:46.200Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9fe0596dd8a9439083538752e6645075 |
| 2756 | 2026-08-14T16:18:46.341Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2757 | 2026-08-14T16:18:46.884Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9fe0596dd8a9439083538752e6645075 |
| 2758 | 2026-08-14T16:18:47.024Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 2759 | 2026-08-14T16:18:47.515Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 2760 | 2026-08-14T16:19:13.461Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 2ddf3ea7e8aa4e518ff248023df2ce57 | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `11`
- Chain head: `e1ea892b06173312c8f1f65eab6c8312035805089612f6b2149f6683f39d85ea`
