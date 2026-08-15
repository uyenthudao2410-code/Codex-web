# Orchestration Run Summary

- Run: `06c80e2ce1464eea8021bdf6f677b312`
- Task: `87240dd37b384765bcde99f813e0d440`
- Objective: Perform an evidence-grounded postmortem of automatic coordination over the last several days (roughly 2026-08-12 through 2026-08-15) in Tools-Codex-web. Determine how much work was actually performed by ChatWeb/Sol control, deterministic Coding Tools MCP, Codex external/deep-code lanes (Mini/Luna/Sol xhigh/Terra), and OpenCode/read-only semantic lanes. Quantify route counts, accepted/rejected/aborted outcomes, external-review attempts/completions/timeouts/capacity failures, TTA where available, current-policy idempotency, proof-cache value, semantic/OpenCode usage, provider/token/estimated-credit economics when recorded, and any gap between intended routing policy and observed behavior. Inspect Git history, orchestration ledger/runtime evidence, performance.json/task history, routing/external-review code, and opencode/codex integration evidence. Do not mutate source. Return explicit caveats where telemetry cannot distinguish ChatWeb reasoning time or OpenCode/Codex activity.
- Status: **active**
- Started: `2026-08-15T03:50:36.404Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `24267839e6474d1cb9fd613414347f05` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `2`
- Chain head: `aade0ab8f9b4953c293732c70c8f8912d21516b5bf92d2f001590515c580cddf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
