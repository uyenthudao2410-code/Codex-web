# Orchestration Run Summary

- Run: `ff6ebabb42cf47d38bfb5a86e569edd6`
- Task: `b4ca23278f334ddfa7cacdb247cb6343`
- Objective: Prepare a one-time fail-closed migration repair for the pre-fix running Coding MCP. Inspect only resources/coding-tools-mcp/scripts/reconcile_execution_resources.py and its focused tests (or nearest execution-resource script tests). Determine the smallest change to (1) include sanitized command_id and owner in remaining active-row diagnostics, and (2) add an explicit opt-in repair flag that can terminate only one live runtime-owned Codex App Server sidecar when its durable managed row strictly matches owner=codex-app-server, command_id prefix codex-app-server-, MEDIUM, empty run_id/wave_id, active lifecycle, PID identity token still matches, and no other non-self active managed work exists. The repair must refuse on ambiguity/mismatch, never terminate arbitrary PID, then reconcile and verify the row terminalized. No writes in prepare.
- Status: **accepted**
- Started: `2026-08-16T14:25:28.009Z`
- Finished: `2026-08-16T14:28:02.903Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `4b5b3d88e5594b80b7be4b2d1da62e2d` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `0148c4a8438347c49f50b3d81eb27107` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 554b4ccff8aa4318b4ef2c704767ef29 | 0148c4a8438347c49f50b3d81eb27107 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 9b088f9f1cd69d4da232ddea4639b6e22365a60e118735c79e2d7d1183fcf966 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8705 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 8699 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `74c4b55b905246b8a5d1d50b0432262734ea3a5dc23b813cea7774271206de3c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
