# Orchestration Wave 1

- Run: `35ebddf53dc34310a8719319b5682f6a`
- Wave: `f8662ab49a694ced90207fa7c41c6922`
- Objective: Verify the live EOCL control loop with a no-write command and record deterministic proof only.
- Mode: `deep_single_lane`
- Base HEAD: `bd87d8bc5c2b1c25f9f9fe5fe3dcb46b29e78fe8`
- Worktree fingerprint: `adc1a53438f05a6d0cc1cd9c6cd6c1e33e7a097a19a6d52a239bbf21957a8812`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 2eeb9264ef5b4fa686c1e6a49efbcc96 | CODEX:sol_xhigh | auto | sol_xhigh | gpt-5.6-sol | xhigh | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 70 | 2026-08-13T05:44:06.251Z | run_started |  | PREFLIGHT |  |
| 71 | 2026-08-13T05:44:06.644Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 72 | 2026-08-13T05:44:06.797Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 73 | 2026-08-13T05:44:07.051Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=deep_single_lane |
| 74 | 2026-08-13T05:44:07.206Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 75 | 2026-08-13T05:44:07.366Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 76 | 2026-08-13T05:44:07.534Z | route_selected | READY | READY | reason=deep_or_broad_context; requested=auto; resolved=sol_xhigh |
| 77 | 2026-08-13T05:44:07.689Z | state_transition | READY | ROUTED | reason=route_selected |
| 78 | 2026-08-13T05:44:07.991Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:sol_xhigh |
| 79 | 2026-08-13T05:44:08.276Z | delegation_finished | ROUTED | ROUTED | reason=candidate_scope_missing; status=blocked |
| 80 | 2026-08-13T05:44:08.430Z | failure_observed | ROUTED | ROUTED | failure_class=CANDIDATE_SCOPE_MISSING |
| 81 | 2026-08-13T05:44:08.609Z | state_transition | ROUTED | REPLAN | reason=CANDIDATE_SCOPE_MISSING; failure_class=CANDIDATE_SCOPE_MISSING |

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
- Events checked: `26`
- Chain head: `a3864601bd463df26adc4b16ba6d0749dc4331410c32b2095ddf03ab4dbd603b`
