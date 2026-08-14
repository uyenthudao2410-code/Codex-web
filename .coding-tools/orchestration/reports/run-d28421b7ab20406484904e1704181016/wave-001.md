# Orchestration Wave 1

- Run: `d28421b7ab20406484904e1704181016`
- Wave: `63e0c3ce85c54fe98b731b303ded7e4f`
- Objective: ONE paid live OpenCode Flash canary, explicitly authorized by the user. Establish a fresh bounded orchestration run/wave only. In execute, run exactly one `npm run canary:opencode-flash` invocation while this exact wave is ROUTED/EXECUTING/PROVING. The canary itself must pass authenticated live preflight first, dispatch exactly once to fixed model opencode-go/deepseek-v4-flash with the fixed read-only package.json prompt and deterministic request_id, poll the same dispatch only, and require a correlated measured UsageEvent with exact model/tokens/provider cost/timing. No Pro. No second provider dispatch or paid retry under any failure condition. No source/settings/service/Git/release mutation.
- Mode: `mcp_only`
- Base HEAD: `bf072d9bd08a14768b729c1d209367bc771633a5`
- Worktree fingerprint: `9477280c386f826cb2e5ea4212a36b94f8d2d735860290ad9319ff24abfbcfe3`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| opencode-provider-3a8e77391776746401a0c337a23ffa532672f58d | opencode | opencode_read_only | opencode-go/deepseek-v4-flash | opencode-go/deepseek-v4-flash |  | completed |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2055 | 2026-08-14T12:49:21.366Z | run_started |  | PREFLIGHT |  |
| 2056 | 2026-08-14T12:49:21.874Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 2057 | 2026-08-14T12:49:31.323Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2058 | 2026-08-14T12:49:31.449Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2059 | 2026-08-14T12:49:31.585Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 2060 | 2026-08-14T12:49:31.666Z | state_transition | READY | ROUTED | reason=route_selected |
| 2061 | 2026-08-14T12:49:32.041Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b010fed1e3ff41abb4f387b12f8340ee |
| 2062 | 2026-08-14T12:49:32.149Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2063 | 2026-08-14T12:49:32.520Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b010fed1e3ff41abb4f387b12f8340ee |
| 2064 | 2026-08-14T12:49:32.658Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 2065 | 2026-08-14T12:49:33.710Z | external_delegation_started | PROVING | PROVING | status=active |
| 2066 | 2026-08-14T12:50:01.681Z | external_delegation_updated | PROVING | PROVING | status=active |
| 2067 | 2026-08-14T12:50:02.215Z | external_delegation_updated | PROVING | PROVING | status=active |
| 2068 | 2026-08-14T12:50:09.765Z | external_delegation_updated | PROVING | PROVING | status=active |
| 2069 | 2026-08-14T12:50:10.139Z | external_delegation_updated | PROVING | PROVING | status=active |
| 2070 | 2026-08-14T12:50:10.231Z | external_delegation_finished | PROVING | PROVING | status=completed |
| 2071 | 2026-08-14T12:50:10.566Z | usage_event |  |  | status=completed |
| 2072 | 2026-08-14T12:50:10.939Z | external_delegation_updated | PROVING | PROVING | status=active |
| 2073 | 2026-08-14T12:50:18.682Z | external_delegation_updated | PROVING | PROVING | status=failed |
| 2074 | 2026-08-14T12:50:19.376Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=cfb38980195a4fd8befe57cfc03573f82b034acf2050b88a07745bd26349873b |
| 2075 | 2026-08-14T12:50:19.482Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 2076 | 2026-08-14T12:50:19.582Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | cfb38980195a4fd8befe57cfc03573f82b034acf2050b88a07745bd26349873b | False | 46344 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `22`
- Chain head: `df842f11e4d6d8c64cddcf75531ebbb83c85c11d8ed0bb337017de8f2c829d3d`
