# Orchestration Wave 2

- Run: `e264f4730cfe429589a6440e5ac7d5b3`
- Wave: `5f63b84fd49b455dbbb4185858a17712`
- Objective: Add a minimal operator-only OpenCode Flash canary utility for Execution Hub activation acceptance without adding any public MCP tool, endpoint, UI, or server contract. The utility must run under Electron solely to decrypt the existing safeStorage MCP bearer in memory, validate it targets the current workspace/runtime, call the existing supervisor-only /__control/hub provider_dispatch/provider_observe actions with identity electron-panel/electron, hardcode model opencode-go/deepseek-v4-flash and a tiny read-only package.json prompt, derive an idempotent request_id from current run_id+wave_id+canary version, poll to one terminal result, then wait for the correlated UsageEvent and emit only a sanitized JSON summary containing IDs/model/status/tokens/cost/timing/measurement. Never print bearer, raw provider result, prompt, stderr, or secret-file contents. Fail closed if current task-projected orchestration state is not ROUTED/EXECUTING/PROVING/ACCEPTING, workspace mismatches, telemetry is absent, model mismatches, or usage/cost is not measured. Add focused Node tests with a fake loopback control server proving authorization is sent but never surfaced, deterministic idempotency, exact Flash-only dispatch, terminal polling, usage correlation, workspace mismatch fail-closed, and sanitized output. Add npm script canary:opencode-flash. Do not run real provider inference in this implementation wave. No UI changes, service restart, settings change, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bf072d9bd08a14768b729c1d209367bc771633a5`
- Worktree fingerprint: `3f6f76506655e2169dadd238eae0bc9545cb5e746163c75ec68b53febb470693`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1953 | 2026-08-14T12:36:25.120Z | wave_replanned |  | PREFLIGHT | reason=The first canary wave was rejected at final acceptance despite green focused tests because paid-call safety did not prove the live MCP runtime target and offered no zero-billing preflight. This replan materially changes the evidence boundary: require authenticated /__control/health workspace/profile/count/instance checks and add a preflight mode that is test-proven to make zero /__control/hub POSTs before allowing paid dispatch. |
| 1954 | 2026-08-14T12:36:25.250Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1955 | 2026-08-14T12:36:25.337Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1956 | 2026-08-14T12:36:25.460Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1957 | 2026-08-14T12:36:25.573Z | state_transition | READY | ROUTED | reason=route_selected |
| 1958 | 2026-08-14T12:36:25.953Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bd5ce6645fb64a21879f0fdf00db7588 |
| 1959 | 2026-08-14T12:36:26.079Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1960 | 2026-08-14T12:36:26.370Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 1961 | 2026-08-14T12:36:26.553Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=bd5ce6645fb64a21879f0fdf00db7588 |
| 1962 | 2026-08-14T12:36:26.663Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
- Events checked: `36`
- Chain head: `19f8541977a1de1a45252fbec5d9fadf23542347a1ffbe2b25b6a769a29c1b98`
