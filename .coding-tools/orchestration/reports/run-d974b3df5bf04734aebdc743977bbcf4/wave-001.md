# Orchestration Wave 1

- Run: `d974b3df5bf04734aebdc743977bbcf4`
- Wave: `1c69e890ea104637859c3781ef68ad9c`
- Objective: Fix only case.py so remaining_capacity(limit, used) returns the non-negative remaining capacity: limit-used when positive, otherwise 0. Do not modify test_case.py. Deterministic oracle: `python test_case.py`. Localized strong-oracle benchmark only.
- Mode: `bounded_candidate`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `e9ba28712186cae6a0a6a4722118ac4bc2ffb7fd69b873da4d7b25aabe09ea5f`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 11c23124aa7442b6be0065968c524b8c | CODEX:mini | mini | mini | gpt-5.4-mini | low | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1302 | 2026-08-14T06:15:01.792Z | run_started |  | PREFLIGHT |  |
| 1303 | 2026-08-14T06:15:02.330Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1304 | 2026-08-14T06:15:02.631Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 1305 | 2026-08-14T06:15:02.834Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1306 | 2026-08-14T06:15:03.009Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1307 | 2026-08-14T06:15:03.243Z | route_selected | READY | READY | reason=explicit_request; requested=mini; resolved=mini |
| 1308 | 2026-08-14T06:15:03.451Z | state_transition | READY | ROUTED | reason=route_selected |
| 1309 | 2026-08-14T06:15:03.813Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:mini |
| 1310 | 2026-08-14T06:15:03.978Z | model_dispatch_started | ROUTED | ROUTED |  |
| 1311 | 2026-08-14T06:15:08.079Z | model_dispatch_finished | ROUTED | ROUTED | status=completed |
| 1312 | 2026-08-14T06:15:08.362Z | delegation_finished | ROUTED | ROUTED | reason=CANDIDATE_TARGET_MISSING; status=blocked |
| 1313 | 2026-08-14T06:15:08.726Z | failure_observed | ROUTED | ROUTED | failure_class=CANDIDATE_TARGET_MISSING |
| 1314 | 2026-08-14T06:15:08.993Z | state_transition | ROUTED | REPLAN | reason=CANDIDATE_TARGET_MISSING; failure_class=CANDIDATE_TARGET_MISSING |

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
- Events checked: `43`
- Chain head: `374e9bd8bd7434cc08e34611d4632ce00084eb2bb0dc53d6c9bb0032fef0122c`
