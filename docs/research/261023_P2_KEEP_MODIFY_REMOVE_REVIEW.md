# P2 review — KEEP / MODIFY / REMOVE for B01–B12 and multi-node expansion

Date: 2026-10-23. Basis: the five retro-captured outcome cases
(`261023_OUTCOME_CASES.md`), the shipped M0–M5 + wave 1–4 mechanisms,
the 2026-10-23 rollback drill, the CI repair runs, and two probes run
for this review (below). Per the assessment's own §14 decision,
B01–B12 are candidates, not commitments: an item is built only when a
real case exposes the gap. This review records, per item, whether the
gap was ever exposed and what already covers it.

## Fresh probe evidence (2026-10-23)

1. **Multi-node store probe.** Against a throwaway Control Plane store
   (temp sqlite, current source), two nodes were enrolled for one owner
   (`probe-node-win`, `probe-node-vm`): distinct device identities and
   secrets issued, `health().counts.nodes == 2`. The suite's HTTP-level
   tests additionally cover two-client routing to a bound node
   (`test_two_oauth_clients_route_exec_to_same_bound_node_and_receipt`,
   green in the 505-test run). The multi-node data path works; nothing
   in production needs a second executor today.
2. **Full-suite state.** MCP suite repaired (CI run history in the
   backlog plan), control-plane suite 505/505 green locally, Work Hub
   file/git suite 19/19 on three machines (wave 4).

## Decisions

| Item | Decision | Evidence |
| --- | --- | --- |
| B01 Worker lifecycle (identity/sleep/wake/status) | **MODIFY — keep as candidate** | Continuation machinery exists and has exactly one live canary run; no second real worker case has appeared. Build the general lifecycle only when one does. |
| B02 Atomic handoff, single claim | **KEEP — covered, no new build** | Capsule handoff + CP writer lease with generations; the auditor lease (gen 2) held exactly one writer through the act_81e2 settlement. |
| B03 Job input ID + uncertain reconciliation | **KEEP — covered, proven live** | Exec journal + receipt reconciliation settled act_81e2 (unknown → rejected with pre-spawn evidence); the designed path, exercised end-to-end on a real incident. |
| B04 Resource references + per-project version | **KEEP — covered** | Project-scope fencing in the Work Hub main process, capsule context binding, recipe/worktree scoping (M1, takeover commits). No cross-project read has been observed since. |
| B05 Agent inbox / delivery + ACK | **MODIFY — keep as candidate** | Action receipts provide ACK semantics for CP actions; a general agent inbox has no case. Revisit if a second messaging surface appears. |
| B06 TaskAttempt owner/generation/lease | **KEEP — covered** | Writer lease generations in the CP store; managed worktrees isolate concurrent writers (M1.3). |
| B07 Source-bound Git / review / acceptance | **KEEP — covered and hardened** | expected_head guard (wave 2), delivery ritual inside commit (wave 3), atomicity vs concurrent writers (wave 4), per-release acceptance records. The strongest-evidenced item in this review. |
| B08 Browser profile/session lifecycle | **MODIFY — keep as candidate** | M3.1 shipped a scoped browser-QA adapter; full profile/session lifecycle management has no case. |
| B09 Plugin capability/health registry | **KEEP — covered in substance** | Skills registry with SHA-256/revision/consumer evidence (M4) and component revision health (M0.2) already separate installed ≠ ready ≠ exposed. Generalize only with a case. |
| B10 Job/restart/tunnel reconciliation | **KEEP — covered, proven repeatedly** | M5 packaged switch, the 2026-10-23 rollback drill in both directions, and the census-gate incident case all exercised restart reconciliation against the same job/epoch identities. |
| B11 Queryable decision memory / provenance | **KEEP — covered in substance** | The `.coding-tools` ledger, outcome cases and acceptance records are the queryable provenance trail; the 5-case retro-capture was produced from them without new tooling. |
| B12 Unified Activity/Result/Attention view | **KEEP — covered** | Work Hub tabs plus the live progress board provide the single activity/result view; M2 coordination states derive from ledger evidence only. |
| Multi-node expansion (topology) | **REMOVE from the active backlog — parked** | Probe 1 proves the mechanism; production topology (1 executor node on Windows, CP host on svhome, this VM) has no queueing pressure and no second executor device doing real work. Re-open trigger: a real second executor joins the tailnet, or an outcome case shows single-node saturation. |

## What this closes

The P2 gate in the backlog plan ("review when cases exist") is now
satisfied: five cases exist, each B-item has an evidence-tied decision,
and no item is silently dropped — MODIFY items stay visible as
candidates with their re-open condition named, and the parked
multi-node item names its trigger. New work enters through outcome
cases, as the outcome doc requires.
