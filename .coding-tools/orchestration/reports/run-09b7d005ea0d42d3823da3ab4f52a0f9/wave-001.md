# Orchestration Wave 1

- Run: `09b7d005ea0d42d3823da3ab4f52a0f9`
- Wave: `3a2d000950864852b3149870ad2abb6f`
- Objective: Fresh H4 Codex exact-usage runtime canary only. Read the current usage persistence path in resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py and resources/coding-tools-mcp/coding_tools_mcp/agent_candidate.py, then report whether complete non-negative integer inputTokens/cachedInputTokens/outputTokens/reasoningOutputTokens from Codex App Server thread/tokenUsage/updated are mapped to a provider UsageEvent. Do not patch, write, adopt, restart, commit, or change source. The purpose is to trigger one bounded Codex candidate lane and then inspect whether exact X/Y/Z/R usage is durably attributed to this RUN/WAVE/delegation.
- Objective revision: `1`
- Objective SHA-256: `12f667e42ef053ae2274d22b25616a431316e3a7bb4cd3c891ad1cf446ba7838`
- Objective source: `run_initial_objective`
- Mode: `bounded_candidate`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `1c9a7d830922437f2180a29ae0cccdc509316b515774b4a41f8bd3cb95a7374e`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| b13f56ebc4454b06a984df1bf49ef2a7 | CODEX:mini | mini | mini | gpt-5.4-mini | low | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36514 | 2026-09-03T06:52:51.565Z | run_started |  | PREFLIGHT |  |
| 36515 | 2026-09-03T06:52:51.942Z | observation_span_recorded |  |  |  |
| 36516 | 2026-09-03T06:52:53.328Z | observation_span_recorded |  |  |  |
| 36517 | 2026-09-03T06:52:53.537Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36518 | 2026-09-03T06:52:53.722Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 36519 | 2026-09-03T06:52:53.913Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36520 | 2026-09-03T06:52:54.088Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36521 | 2026-09-03T06:52:54.308Z | route_selected | READY | READY | reason=explicit_request; requested=mini; resolved=mini |
| 36522 | 2026-09-03T06:52:54.504Z | state_transition | READY | ROUTED | reason=route_selected |
| 36523 | 2026-09-03T06:52:54.715Z | observation_span_recorded |  |  |  |
| 36524 | 2026-09-03T06:52:55.080Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:mini |
| 36525 | 2026-09-03T06:52:55.306Z | model_dispatch_started | ROUTED | ROUTED |  |
| 36526 | 2026-09-03T06:52:55.949Z | model_dispatch_finished | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE; status=error |
| 36527 | 2026-09-03T06:52:56.261Z | delegation_finished | ROUTED | ROUTED | reason=PROMPT_TOO_LARGE; status=blocked |
| 36528 | 2026-09-03T06:52:56.453Z | failure_observed | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE |
| 36529 | 2026-09-03T06:52:56.686Z | state_transition | ROUTED | REPLAN | reason=PROMPT_TOO_LARGE; failure_class=PROMPT_TOO_LARGE |
| 36530 | 2026-09-03T06:52:56.929Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `37`
- Chain head: `85e931be8e82fa7e53c9650f041eb6fb64c40f26fcabc967c6a15ec59685d9b7`
