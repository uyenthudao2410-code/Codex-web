# Orchestration Wave 2

- Run: `01f754053c014a5eac93dd7db29b8c9c`
- Wave: `3f8ea6a03cd545f485dcc1f44d7bbf84`
- Objective: Fix bounded Mini/Luna candidate packet localization for deep symbols in large files. Preserve the 14k source-evidence budget: reserve a bounded portion for unique query-centered snippets read around search match line numbers on allowed_paths, count snippet content against the same remaining budget, then fill remaining budget with existing head-of-file slices. Keep existing compact search metadata. Ignore invalid/out-of-scope matches fail-closed. Add a focused regression test where the target symbol is after line 2000 so prepare_coding_context truncates the file head but the candidate packet still contains an exact local snippet around the deep match. Do not change routing thresholds or candidate write authority.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `8b9c887bca0e68dce83b9e8f5aaaa8d4ff5186c868ac46f5cc4c62bf19fcad69`
- Contract fingerprint: `11df88222009874c4facb02f5742cd1f3837dbba9dcc92d2ad1fc7064dad6db8`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 845 | 2026-08-14T04:05:22.687Z | wave_replanned |  | PREFLIGHT | reason=Final acceptance rejected the first green wave because short snippets could cause up to 18 deep file scans even though payload characters were bounded. This wave adds a strict four-snippet cap and changes the test evidence to include five distinct deep query matches, proving I/O boundedness as well as deep-symbol visibility. |
| 846 | 2026-08-14T04:05:22.831Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 847 | 2026-08-14T04:05:22.987Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 848 | 2026-08-14T04:05:23.151Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 849 | 2026-08-14T04:05:23.269Z | state_transition | READY | ROUTED | reason=route_selected |
| 850 | 2026-08-14T04:05:23.734Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3684427148fc4131b759904603baf93a |
| 851 | 2026-08-14T04:05:23.902Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 852 | 2026-08-14T04:05:24.378Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_CONTEXT_NOT_FOUND |
| 853 | 2026-08-14T04:05:24.616Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=3684427148fc4131b759904603baf93a |
| 854 | 2026-08-14T04:05:24.751Z | state_transition | EXECUTING | REPLAN | reason=PATCH_CONTEXT_NOT_FOUND; failure_class=PATCH_CONTEXT_NOT_FOUND |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `fad8716b68d62239b84b555f291231b4318c5e2368e54533089cd76a9c151784`
