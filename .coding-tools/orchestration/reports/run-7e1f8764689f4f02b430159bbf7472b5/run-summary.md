# Orchestration Run Summary

- Run: `7e1f8764689f4f02b430159bbf7472b5`
- Task: `07161a27dab0447a889cb7e72f0aa95f`
- Objective: Adopt exact existing bytes for the authorized 17-file PRL v12 / Revision-4 closure packet on base a357e1bb45a68cfaf25b8a2aa99a133ab256102c without rewriting any file; preserve unrelated WIP and .coding-tools evidence; run the authorized exact proof commands and advance this same EOCL RUN/WAVE only.
- Status: **aborted**
- Started: `2026-08-31T03:34:27.735Z`
- Finished: `2026-08-31T14:00:42.890Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `cfdd78e90c244193ad45bd5b75f75b5a` | 1 | `run_initial_objective` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | replanned |
| 2 | `4cfb65cf59c043e2a25abf4ce63dcc9d` | 2 | `replan_request` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32965 | `deterministic` | `deterministic` | explicit_request |
| 33009 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 33002 | `SOL_REJECTED` | `ACCEPTING` | EXACT_17_FILE_RECEIPTS_MISSING |
| 33057 | `SOL_REJECTED` | `ACCEPTING` | EXACT_WAVE_PROOF_REQUIRED_AFTER_ADOPTION |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `65`
- Chain head: `ca0f4d876a55d7a90975e012c8128ea9e4edea3c85a0fab50afe82948153752e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
