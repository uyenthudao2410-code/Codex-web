# Orchestration Wave 1

- Run: `ff4a12a96ce549d4871195fc9d77428f`
- Wave: `230cf42e1a264631a86c5af3692d3205`
- Objective: Complete the remaining non-UI technical roadmap for Tools-Codex-web without changing the Smart-v3 public 8-tool contract. Implement a canonical measured UsageEvent contract/projection with provenance, measured-vs-estimated identity, cached/reasoning token counters, queue/provider/total timing and typed provider error classification; integrate existing OpenCode telemetry into that contract. Implement a Hub-side OpenCode read-only Provider Adapter that can dispatch an explicitly selected allowlisted OpenCode Go model (Flash/Pro) with a bounded prompt packet, timeout/cancel lifecycle, exact run/wave/session/model correlation, usage/cost capture, and fail-closed no-native-write semantics. Implement shadow provider routing as recommendation/evidence only (no automatic mutation or controller transfer), with durable accepted-task route/economics fields sufficient for later cohort calibration. Preserve current controller/write fencing, current routing thresholds, OpenCode worker-only role, existing concurrent UI work, and existing exact telemetry semantics. Do not touch renderer/UI files, do not restart Electron/runtime, do not change permission settings, do not run paid/provider inference solely for proof, and do not commit/push/release/deploy.
- Mode: `deep_single_lane`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `2f496c0edd29d1013afb3daa44ea4300d2bfcb923286768df8d4f4ff9619fe9b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| d056147ab09c49fcbf6cd309107e3999 | CODEX:sol_xhigh | sol_xhigh | sol_xhigh | gpt-5.6-sol | xhigh | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1724 | 2026-08-14T09:34:38.774Z | run_started |  | PREFLIGHT |  |
| 1725 | 2026-08-14T09:34:39.620Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1726 | 2026-08-14T09:37:12.032Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 1727 | 2026-08-14T09:37:12.273Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1728 | 2026-08-14T09:37:12.474Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1729 | 2026-08-14T09:37:12.683Z | route_selected | READY | READY | reason=explicit_request; requested=sol_xhigh; resolved=sol_xhigh |
| 1730 | 2026-08-14T09:37:12.844Z | state_transition | READY | ROUTED | reason=route_selected |
| 1731 | 2026-08-14T09:37:13.161Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:sol_xhigh |
| 1732 | 2026-08-14T09:37:13.401Z | delegation_finished | ROUTED | ROUTED | reason=candidate_scope_missing; status=blocked |
| 1733 | 2026-08-14T09:37:13.676Z | failure_observed | ROUTED | ROUTED | failure_class=CANDIDATE_SCOPE_MISSING |
| 1734 | 2026-08-14T09:37:13.817Z | state_transition | ROUTED | REPLAN | reason=CANDIDATE_SCOPE_MISSING; failure_class=CANDIDATE_SCOPE_MISSING |

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
- Events checked: `41`
- Chain head: `98be1f371f0f6a3a76beb00d30c943e7e27fef27d4e71efeb254dab6e4fa67ed`
