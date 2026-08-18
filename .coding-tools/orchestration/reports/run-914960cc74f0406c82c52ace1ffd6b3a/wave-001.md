# Orchestration Wave 1

- Run: `914960cc74f0406c82c52ace1ffd6b3a`
- Wave: `af55d1a28cc24c258acf1845cc46b33f`
- Objective: Continue Layer C after accepted C1a on the current authoritative checkout. Wire explicit compute_placement_policy guards into run_readonly_validation and run_readonly_validation_agent; explicit selector only for long unsandboxed Agent-backed structured-job capable clean exact-source cargo_check/test. Implement local_only forcing source with no remote target selection and server_preferred using existing clean target selection/revalidation plus source fallback. Build ShellJobValidationComputePlacement from actual executor, persist it in ShellJobValidationMetadata and ValidationHandoff. Do not yet add tests in this wave beyond compile proof; selector absent must preserve current auto-offload behavior. Preserve all telemetry/concurrent commits. No analyzer/manifest/restart/P3 enrollment.
- Mode: `deep_single_lane`
- Base HEAD: `17e87d34b159cbc175a77bb041e670000c9f7f4b`
- Worktree fingerprint: `e86891942b708998507d2eb9103f4ef1349a970474e477f896d97fb0a43f8631`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 9cc6c6070d7a402082a96418341dd41b | CODEX:sol_xhigh | sol_xhigh | sol_xhigh | gpt-5.6-sol | xhigh | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16307 | 2026-08-18T00:23:22.135Z | run_started |  | PREFLIGHT |  |
| 16308 | 2026-08-18T00:23:27.195Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16309 | 2026-08-18T00:25:52.854Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16310 | 2026-08-18T00:25:52.971Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 16311 | 2026-08-18T00:25:53.194Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=mcp_only; resolved=deep_single_lane |
| 16312 | 2026-08-18T00:25:53.328Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16313 | 2026-08-18T00:25:53.445Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16314 | 2026-08-18T00:25:53.569Z | route_selected | READY | READY | reason=explicit_request; requested=sol_xhigh; resolved=sol_xhigh |
| 16315 | 2026-08-18T00:25:53.701Z | state_transition | READY | ROUTED | reason=route_selected |
| 16316 | 2026-08-18T00:25:53.921Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:sol_xhigh |
| 16317 | 2026-08-18T00:25:54.050Z | model_dispatch_started | ROUTED | ROUTED |  |
| 16318 | 2026-08-18T00:26:24.785Z | model_dispatch_finished | ROUTED | ROUTED | status=interrupted |
| 16319 | 2026-08-18T00:26:24.978Z | delegation_finished | ROUTED | ROUTED | reason=candidate_model_not_completed; status=blocked |
| 16320 | 2026-08-18T00:26:25.108Z | failure_observed | ROUTED | ROUTED | failure_class=CANDIDATE_MODEL_NOT_COMPLETED |
| 16321 | 2026-08-18T00:26:25.227Z | state_transition | ROUTED | REPLAN | reason=CANDIDATE_MODEL_NOT_COMPLETED; failure_class=CANDIDATE_MODEL_NOT_COMPLETED |
| 16322 | 2026-08-18T00:26:25.368Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `105`
- Chain head: `35dc75a3c181ef05008301c28a66e545f0d1f1626e437e6c88d18e4d60fcfe12`
