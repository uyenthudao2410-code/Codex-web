# Orchestration Wave 2

- Run: `bb08c0c80a25491dbd457a9817c7f1e2`
- Wave: `38c1c11276f649d285014715ef9a588d`
- Objective: T2.1 TruthSnapshot integration repair continuation only: after fixing the unsupported `wave=` keyword, the active-wave regression exposed a second bug on the same fallback path: `_operator_truth_snapshot` selects the latest ledger wave when task projection lacks wave_id but continues to emit the empty projected wave_id. Derive `selected_wave_id` from the selected ledger wave (falling back to projected wave_id), use it for `wave_objective_provenance`, and emit it in the TruthSnapshot orchestration identity. Keep the strengthened regression unchanged. No other production behavior or scope expansion.
- Objective revision: `2`
- Objective SHA-256: `d11c1afc987f69aaa01b4f9f6980ddc355a7cd33f1924ae80665e54ddd33cb54`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9eb05072e54ffca9576e23c2d4a4f4e14034bddc`
- Worktree fingerprint: `87e50fccecdb18418e080235a97bea53a8178d724ef8c1eedfe1fa287a692e4f`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26268 | 2026-08-21T08:03:22.004Z | wave_replanned |  | PREFLIGHT | reason=First T2.1 wave removed the HTTP TypeError but the strengthened active-wave regression proved the same fallback path loses the selected ledger wave ID when task projection has none. Changed evidence justifies a replacement wave: derive and use selected_wave_id consistently for lookup and output. |
| 26269 | 2026-08-21T08:03:22.693Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26270 | 2026-08-21T08:03:58.620Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26338 | 2026-08-21T20:34:48.728Z | state_transition | PREFLIGHT | ABORTED | reason=Terminalize historical stale T2.1 run without deleting history. Audit shows failed proof, zero accepted checkpoints, and an active PREFLIGHT replacement wave; the corrected T2.1 work was later accepted canonically in run df773562c37d42e6ae5c90505544e408. This run was just incorrectly adopted by a different auto-started task via workspace-global fallback, so it must not remain active or be reused as lineage. |
| 26339 | 2026-08-21T20:34:49.118Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `25`
- Chain head: `9477966f921405f9a6f7493d1814c9cfbaba5cf0bbe0004dc9a6729b012a8a9d`
