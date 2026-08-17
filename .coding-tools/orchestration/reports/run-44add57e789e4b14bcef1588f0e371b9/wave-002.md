# Orchestration Wave 2

- Run: `44add57e789e4b14bcef1588f0e371b9`
- Wave: `78a350d948404e688623539764c0c0cf`
- Objective: P0.2 preflight and real Scheduled Task installation from the already fresh controlled acceptance app. Do not change source or rebuild. Require HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, acceptance root present, installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420, Scheduled Task absent, supervisor root absent, healthy existing Recovery Host descriptor/process, and exactly one listener on each 18766/18767/18082/18083. Capture current Recovery Host PID+instance as the immutable baseline for this installed-session acceptance. Then invoke the installed supervisor -Action Install with installed app executable/AppRoot/Packaged and verify task structure: same current user, Interactive logon, Limited run level, fixed PowerShell action referencing %LOCALAPPDATA%\WebMcpRecoverySupervisor\recovery-supervisor.ps1 with -Action Run, two triggers, manifest mode packaged, manifest arguments exactly ['--recovery-host'], manifest executable/hash match installed app, installed supervisor copy hash exact. Return only content-free identities and task structure, never descriptor token.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12777 | 2026-08-17T08:49:11.111Z | wave_replanned |  | PREFLIGHT | reason=The previous wave failed only because the verification PowerShell used `throw'...'` without whitespace, producing CommandNotFoundException after supervisor Install had already run. This wave does not retry Install; it verifies the resulting external state with corrected shell syntax. |
| 12778 | 2026-08-17T08:49:11.698Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12779 | 2026-08-17T08:49:11.922Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12780 | 2026-08-17T08:49:12.115Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12781 | 2026-08-17T08:49:12.277Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12782 | 2026-08-17T08:49:12.494Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12783 | 2026-08-17T08:49:12.671Z | state_transition | READY | ROUTED | reason=route_selected |
| 12784 | 2026-08-17T08:49:13.277Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=66888f55c302414b8a82c078724a8794 |
| 12785 | 2026-08-17T08:49:13.445Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12786 | 2026-08-17T08:49:14.012Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=66888f55c302414b8a82c078724a8794 |
| 12787 | 2026-08-17T08:49:14.229Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12788 | 2026-08-17T08:49:14.777Z | proof_cache_miss |  |  | reason=cold; stage_id=check:afc3c2e41b8225af; input_fingerprint=f46d40a45612b4f56a000a6b08fadc35b3b49bc7587969d250707d6942bd2f4a |
| 12789 | 2026-08-17T08:49:15.165Z | managed_process_admitted |  |  | owner=default |
| 12790 | 2026-08-17T08:49:15.506Z | managed_process_started |  |  | owner=default |
| 12791 | 2026-08-17T08:49:17.323Z | managed_process_terminal |  |  | owner=default |
| 12792 | 2026-08-17T08:49:17.706Z | proof_recorded |  |  | stage_id=check:afc3c2e41b8225af; status=failed; cache_hit=False; input_fingerprint=f46d40a45612b4f56a000a6b08fadc35b3b49bc7587969d250707d6942bd2f4a |
| 12793 | 2026-08-17T08:49:17.892Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 12794 | 2026-08-17T08:49:18.047Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 12795 | 2026-08-17T08:49:18.223Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:afc3c2e41b8225af | failed | f46d40a45612b4f56a000a6b08fadc35b3b49bc7587969d250707d6942bd2f4a | False | 2554 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `62`
- Chain head: `52ffb533cbbd15df0a7b36408c47f0603635ea682fdea9e7d8720b85910e4a29`
