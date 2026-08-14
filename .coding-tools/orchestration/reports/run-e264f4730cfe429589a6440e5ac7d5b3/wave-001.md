# Orchestration Wave 1

- Run: `e264f4730cfe429589a6440e5ac7d5b3`
- Wave: `f6876df9fe664471b19d78883066e07f`
- Objective: Add a minimal operator-only OpenCode Flash canary utility for Execution Hub activation acceptance without adding any public MCP tool, endpoint, UI, or server contract. The utility must run under Electron solely to decrypt the existing safeStorage MCP bearer in memory, validate it targets the current workspace/runtime, call the existing supervisor-only /__control/hub provider_dispatch/provider_observe actions with identity electron-panel/electron, hardcode model opencode-go/deepseek-v4-flash and a tiny read-only package.json prompt, derive an idempotent request_id from current run_id+wave_id+canary version, poll to one terminal result, then wait for the correlated UsageEvent and emit only a sanitized JSON summary containing IDs/model/status/tokens/cost/timing/measurement. Never print bearer, raw provider result, prompt, stderr, or secret-file contents. Fail closed if current task-projected orchestration state is not ROUTED/EXECUTING/PROVING/ACCEPTING, workspace mismatches, telemetry is absent, model mismatches, or usage/cost is not measured. Add focused Node tests with a fake loopback control server proving authorization is sent but never surfaced, deterministic idempotency, exact Flash-only dispatch, terminal polling, usage correlation, workspace mismatch fail-closed, and sanitized output. Add npm script canary:opencode-flash. Do not run real provider inference in this implementation wave. No UI changes, service restart, settings change, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bf072d9bd08a14768b729c1d209367bc771633a5`
- Worktree fingerprint: `bab6857e11e8ce4c565b06921150e2bf0f9424daa571720646d439230320fc55`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1939 | 2026-08-14T12:31:27.939Z | run_started |  | PREFLIGHT |  |
| 1940 | 2026-08-14T12:31:28.259Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1941 | 2026-08-14T12:31:28.355Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1942 | 2026-08-14T12:31:28.438Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1943 | 2026-08-14T12:31:28.522Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1944 | 2026-08-14T12:31:28.639Z | state_transition | READY | ROUTED | reason=route_selected |
| 1945 | 2026-08-14T12:31:28.989Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1112ea8cfd8e4bc98a4564f7953720e7 |
| 1946 | 2026-08-14T12:31:29.081Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1947 | 2026-08-14T12:31:29.606Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1112ea8cfd8e4bc98a4564f7953720e7 |
| 1948 | 2026-08-14T12:31:29.731Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1949 | 2026-08-14T12:31:43.472Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f084ebe1c7de2294f1e086e27ebdbb80a0cdc52d704d4b0fe7ac79d0472187ab |
| 1950 | 2026-08-14T12:31:53.672Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1951 | 2026-08-14T12:35:15.704Z | failure_observed | ACCEPTING | ACCEPTING | reason=Focused proof is green and audit integrity passes, but the paid-canary acceptance boundary is not yet fail-closed enough: the utility validates Electron settings workspace but does not mandatorily compare the live MCP /__control/health workspace/runtime before dispatch, and it lacks a non-billing preflight that proves safeStorage + live runtime targeting with zero provider_dispatch calls. Tighten those two gates before any paid inference.; failure_class=SOL_REJECTED |
| 1952 | 2026-08-14T12:35:15.820Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | f084ebe1c7de2294f1e086e27ebdbb80a0cdc52d704d4b0fe7ac79d0472187ab | False | 13344 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `19f8541977a1de1a45252fbec5d9fadf23542347a1ffbe2b25b6a769a29c1b98`
