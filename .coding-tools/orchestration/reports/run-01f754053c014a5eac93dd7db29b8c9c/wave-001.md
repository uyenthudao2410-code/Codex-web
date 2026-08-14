# Orchestration Wave 1

- Run: `01f754053c014a5eac93dd7db29b8c9c`
- Wave: `fc954bb3cf6e4040ae8e708e0fdcb0da`
- Objective: Fix bounded Mini/Luna candidate packet localization for deep symbols in large files. Preserve the 14k source-evidence budget: reserve a bounded portion for unique query-centered snippets read around search match line numbers on allowed_paths, count snippet content against the same remaining budget, then fill remaining budget with existing head-of-file slices. Keep existing compact search metadata. Ignore invalid/out-of-scope matches fail-closed. Add a focused regression test where the target symbol is after line 2000 so prepare_coding_context truncates the file head but the candidate packet still contains an exact local snippet around the deep match. Do not change routing thresholds or candidate write authority.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `8c6a1cf738333a26a1e31a3490f8b091d7631269376205ed2a8c09c6d8358a45`
- Contract fingerprint: `4f49a2bfc3e1e8f152e088bd08f6e01b43ce7c1c1c0482c93b42e0e31e0bfdde`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 832 | 2026-08-14T04:04:37.518Z | run_started |  | PREFLIGHT |  |
| 833 | 2026-08-14T04:04:37.694Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 834 | 2026-08-14T04:04:37.860Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 835 | 2026-08-14T04:04:38.016Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 836 | 2026-08-14T04:04:38.319Z | state_transition | READY | ROUTED | reason=route_selected |
| 837 | 2026-08-14T04:04:38.926Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3a5cf9dce3b443f9b43663d523bbf2de |
| 838 | 2026-08-14T04:04:39.108Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 839 | 2026-08-14T04:04:39.757Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3a5cf9dce3b443f9b43663d523bbf2de |
| 840 | 2026-08-14T04:04:39.909Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 841 | 2026-08-14T04:04:43.718Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=d547a51f856b0f80edd2513e79b32be71d61254cd7d0d33c7347142a1a23f999 |
| 842 | 2026-08-14T04:04:44.096Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 843 | 2026-08-14T04:05:03.324Z | failure_observed | ACCEPTING | ACCEPTING | reason=Final efficiency review found one boundedness improvement before acceptance: the 6k snippet character budget limits payload size but very short snippets could still trigger up to 18 deep read_file scans (6 queries x 3 matches). Add an explicit maximum of 4 unique query-centered snippets so candidate packet I/O is deterministically bounded while preserving the new deep-symbol evidence behavior.; failure_class=SOL_REJECTED |
| 844 | 2026-08-14T04:05:03.492Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | d547a51f856b0f80edd2513e79b32be71d61254cd7d0d33c7347142a1a23f999 | False | 3282 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `fad8716b68d62239b84b555f291231b4318c5e2368e54533089cd76a9c151784`
