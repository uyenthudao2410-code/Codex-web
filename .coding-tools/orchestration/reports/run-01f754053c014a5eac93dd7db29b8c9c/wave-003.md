# Orchestration Wave 3

- Run: `01f754053c014a5eac93dd7db29b8c9c`
- Wave: `5ca5392b1ce44462a8a1a1d93043c579`
- Objective: Fix bounded Mini/Luna candidate packet localization for deep symbols in large files. Preserve the 14k source-evidence budget: reserve a bounded portion for unique query-centered snippets read around search match line numbers on allowed_paths, count snippet content against the same remaining budget, then fill remaining budget with existing head-of-file slices. Keep existing compact search metadata. Ignore invalid/out-of-scope matches fail-closed. Add a focused regression test where the target symbol is after line 2000 so prepare_coding_context truncates the file head but the candidate packet still contains an exact local snippet around the deep match. Do not change routing thresholds or candidate write authority.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `8b9c887bca0e68dce83b9e8f5aaaa8d4ff5186c868ac46f5cc4c62bf19fcad69`
- Contract fingerprint: `11df88222009874c4facb02f5742cd1f3837dbba9dcc92d2ad1fc7064dad6db8`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 855 | 2026-08-14T04:05:45.731Z | wave_replanned |  | PREFLIGHT | reason=The previous replan patch was atomically rejected because one loop hunk used non-matching blank-line context. Targeted read-only inspection now provides the exact current loop and test context. Apply the same four-snippet cap design with these exact hunks and rerun the focused oracle. |
| 856 | 2026-08-14T04:05:45.930Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 857 | 2026-08-14T04:05:46.070Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 858 | 2026-08-14T04:05:46.303Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 859 | 2026-08-14T04:05:46.486Z | state_transition | READY | ROUTED | reason=route_selected |
| 860 | 2026-08-14T04:05:47.039Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6ba4d486907f4c1cba63a7be9d4f0c56 |
| 861 | 2026-08-14T04:05:47.233Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 862 | 2026-08-14T04:05:47.881Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6ba4d486907f4c1cba63a7be9d4f0c56 |
| 863 | 2026-08-14T04:05:48.069Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 864 | 2026-08-14T04:05:52.756Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2e976237127e0e01f6376903914c4068450e1b67b8aecf5308589691d99f8f63 |
| 865 | 2026-08-14T04:05:53.122Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 866 | 2026-08-14T04:06:57.730Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 2e976237127e0e01f6376903914c4068450e1b67b8aecf5308589691d99f8f63 | False | 4063 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 0b4ce073a4a74da7a23f061f08a947b5 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | fe80ea00804b96d3167a7c292f5e0adbbde30f66677c62b5792665f1c7d2ba64 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `fad8716b68d62239b84b555f291231b4318c5e2368e54533089cd76a9c151784`
