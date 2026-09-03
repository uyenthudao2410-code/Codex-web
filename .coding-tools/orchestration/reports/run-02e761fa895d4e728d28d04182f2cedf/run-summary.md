# Orchestration Run Summary

- Run: `02e761fa895d4e728d28d04182f2cedf`
- Task: `b88c613de61643e9a076dc25a3472b7a`
- Objective: Apply TG1-TG12 Stage B V4 exact-write packet to the authoritative dirty workspace and prove changed behavior
- Status: **accepted**
- Started: `2026-09-03T04:34:07.234Z`
- Finished: `2026-09-03T06:39:15.290Z`

## Outcome metrics

- Waves: **8**
- Route decisions: **8**
- Failures observed: **7**
- REPLAN transitions: **7**
- Proof stages: **12**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `7a0f8ffa3dfd473bbbcb791922503763` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `0a022bf9e46d44a8ab535ccc567c0851` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `349c2d6c8b8040bfbc312800897c5e8a` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 4 | `24f0289cac394f16956fc46a50b6e6e8` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 5 | `7e3c5f6efb1d4fb9ba8e478782de5f9a` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 6 | `d1b0fb319f8c491b8e79b2df27384b2f` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 7 | `b738660bc26146fe90ac0fbc8ec9e621` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 8 | `55ccbd84854746ea94f857a274ad7b52` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| db3552a968d74562ad446f2c276a2063 | 55ccbd84854746ea94f857a274ad7b52 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | c5cd3ef913f0cbed8255378047f77f7c7f5ff17552bbde66635322bf9f99b810 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 36058 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 36083 | `deterministic` | `deterministic` | explicit_request |
| 36103 | `deterministic` | `deterministic` | explicit_request |
| 36128 | `deterministic` | `deterministic` | explicit_request |
| 36162 | `deterministic` | `deterministic` | explicit_request |
| 36239 | `deterministic` | `deterministic` | explicit_request |
| 36349 | `deterministic` | `deterministic` | explicit_request |
| 36459 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 36073 | `CHECK_FAILED` | `PROVING` |  |
| 36093 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 36118 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 36152 | `CHECK_FAILED` | `PROVING` |  |
| 36195 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance exact-SHA attestations were rejected because this proof-only wave has no durable 52-file mutation/adoption surface. Replan to adopt the already-written exact 52 postimages under a scoped lease without rewriting them, run a current-wave proof, then accept with matching 52 SHA attestations. |
| 36245 | `ACCEPTANCE_FILE_SHA_MISMATCH` | `EXECUTING` |  |
| 36374 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `222`
- Chain head: `acc5c5cbb29137c03d5a1a3cc7eb065d17c4bf71f5f9072787acf4f4896feb6c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
