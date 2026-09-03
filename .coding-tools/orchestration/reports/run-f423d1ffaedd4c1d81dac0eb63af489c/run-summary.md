# Orchestration Run Summary

- Run: `f423d1ffaedd4c1d81dac0eb63af489c`
- Task: `3d78c5a186c046c4b081fc0bee1f8998`
- Objective: Continue the existing evidence-only baseline roll-forward RUN/WAVE. Do not modify source or runtime. Prove current HEAD and Coding MCP correctness with module-size guard, repository diff check, and the full pytest suite. Preserve all dirty WIP and .coding-tools evidence; do not touch unbound job 71f8e9646b644839bbd4f95be7dba7d5. This proof will be followed only if green by exact current-byte final-acceptance attestations for the independently recomputed untrusted coding_mcp baseline paths.
- Status: **accepted**
- Started: `2026-09-01T01:26:47.869Z`
- Finished: `2026-09-01T03:47:47.447Z`

## Outcome metrics

- Waves: **6**
- Route decisions: **6**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **12**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `8b8b0cf40c7d45c5b3aa4243d264b745` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `16ee3b32894d463fbb93ebcc8d383464` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `7c7dd7cd05ad4ecbafa39dd61dba26c4` | 3 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 4 | `adb16c9fae494521b959144922fcda54` | 4 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 5 | `0746c50d1fb9449f80513758c9b25deb` | 5 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 6 | `d3d9374a397a48538fe5c18247679d7a` | 6 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 73b066b0192f416f8e4d8107bf3397d6 | d3d9374a397a48538fe5c18247679d7a | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 99567d5b8d761df581642dc0a45b65e410484d3e9f458ba3f2afbda8f854fb2d | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 33943 | `deterministic` | `deterministic` | explicit_request |
| 34116 | `deterministic` | `deterministic` | explicit_request |
| 34174 | `deterministic` | `deterministic` | explicit_request |
| 34188 | `deterministic` | `deterministic` | explicit_request |
| 34225 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 34243 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 34109 | `SOL_REJECTED` | `ACCEPTING` | ACCEPTANCE_FILE_ATTESTATION_REQUIRED — final acceptance proved two pre-existing dirty acceptance paths lack durable current-lineage provenance: resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py and resources/coding-tools-mcp/tests/test_problem_lineage.py. Replan the SAME RUN only to adopt these exact current bytes without content mutation; preserve the existing green proof authority and do not create a new RUN. |
| 34161 | `SOL_REJECTED` | `ACCEPTING` | ACCEPTANCE_PROOF_REQUIRED: provenance-only adoption succeeded, but proof lineage was not materialized in the adoption wave. |
| 34180 | `EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED` | `EXECUTING` |  |
| 34218 | `CHECK_FAILED` | `PROVING` |  |
| 34236 | `INVALID_ARGUMENT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `204`
- Chain head: `855850803062800611e9d45e3c4ddd2517e83caefea8b866fb59ecf9ff4bddbf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
