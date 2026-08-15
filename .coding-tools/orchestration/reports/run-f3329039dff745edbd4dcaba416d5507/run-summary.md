# Orchestration Run Summary

- Run: `f3329039dff745edbd4dcaba416d5507`
- Task: `38aa573c03914b1199a766967f91f390`
- Objective: Finalize proof for the accepted-result measurement and paired-policy evaluation plane already written in the prior wave. Do not mutate source in this wave. Verify normalized accepted-result evaluation, paired representative policy comparison, evaluation schema, CLI availability, and whitespace integrity.
- Status: **accepted**
- Started: `2026-08-15T04:20:06.551Z`
- Finished: `2026-08-15T04:20:56.339Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `b466227c76f843c385d8c01e3a704978` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `91fe049e7fb54695985384083d2f3258` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 30a4b3902fb2429d95a5f1696d072398 | 91fe049e7fb54695985384083d2f3258 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | bf2dde76c9c0c551076e468c0e1ca4b0313515ce936aca382597e6bf32097d3c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4143 | `deterministic` | `deterministic` | explicit_request |
| 4156 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4151 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `bd57a78c50dbc7d98e4e3ecfcbe996ac6f04173a681c46c710fd54bac2b1af01`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
