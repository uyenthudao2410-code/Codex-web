# Orchestration Run Summary

- Run: `f5e910d40935469aa9f468bcd760883d`
- Task: `c829ff1c076842eab43d01f7e6ba4498`
- Objective: Investigate Project Finance -> Project detail -> Overview in the HR app. Identify every overview KPI/card/table value that is currently hardcoded, mocked, placeholder, seeded only for UI, or falls back to fake numbers. Trace the real data contracts and calculation sources available in the current finance frontend/BFF/backend. Do not mutate files yet. Financial invariant: displayed monetary/percentage/status values must be derived from the selected project's real persisted/read-model data and must not fabricate a value when source data is missing; missing data should be represented truthfully. Return the smallest coherent implementation scope and authoritative focused verification commands.
- Status: **accepted**
- Started: `2026-08-19T04:28:36.634Z`
- Finished: `2026-08-19T04:45:55.058Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **2**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6053bb07f27949cb9c21c14017142799` | `mcp_only` | `06854413b465b17749346ecfd7ce51731b6a4789` | replanned |
| 2 | `986f52e5cba643178e2a8d66031be9a1` | `mcp_only` | `788c0f33470611be3d50727a5b23c29ef2169070` | replanned |
| 3 | `f95772cdfb674d0a86a0d793b3bb381a` | `mcp_only` | `06854413b465b17749346ecfd7ce51731b6a4789` | replanned |
| 4 | `d871a92609e342b4b7c08ed46cc67fa2` | `mcp_only` | `788c0f33470611be3d50727a5b23c29ef2169070` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f67dbf0c9b434b75a349e4d8cf9e5a54 | d871a92609e342b4b7c08ed46cc67fa2 | accepted | 788c0f33470611be3d50727a5b23c29ef2169070 | 0ff3c8defc6187c288a2fa80ae5096248961cbe4d9632f3c4ec176fc7d30eaca | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 19251 | `deterministic` | `deterministic` | explicit_request |
| 19450 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 19243 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 19269 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 19273 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 19366 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `197`
- Chain head: `b7269eb4089c09255400b81b4981a53bcbe1a4a2fccfe75cabcc724afe37087e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
