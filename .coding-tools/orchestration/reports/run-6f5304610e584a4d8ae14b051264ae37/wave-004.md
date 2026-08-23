# Orchestration Wave 4

- Run: `6f5304610e584a4d8ae14b051264ae37`
- Wave: `9f115e794bbe4de39ddc902dde351460`
- Objective: Resolve the bounded final-acceptance blocker in the ledger maintenance path for the E:\DEV\Codex-web project. Preserve already-accepted P0/P1/P3 behavior. Fix compact_ledger so a WAL-mode writer or maintenance blocker that appears after initial preflight but before destructive os.replace causes a fail-closed abort. Add a fresh just-before-replace inspection/state-identity validation that rechecks controller leases, managed jobs, write fences, compact_allowed, and logical database identity rather than trusting only the main sqlite file SHA. Make source drift detection WAL-aware and ensure no silent retry. Add durable replacement handling: fsync/flush the replacement database before os.replace and perform the strongest safe parent-directory durability step supported by the platform without making Windows behavior brittle; document/code the platform contract if directory fsync is unsupported. Add regression tests that deterministically inject a late lease/job/fence or WAL write after preflight and prove os.replace is not called, plus tests for durability helper behavior where practical. Re-run the existing ledger maintenance tests and the affected ledger-analysis/idempotency/report suites, then a broader relevant package test boundary and git diff --check/module-size checks. Do not restart services, do not compact the canonical live ledger, do not append smoke records, do not commit, stage, push, reset, or revert unrelated worktree changes. Continue the same EOCL run after the prior NOT_ACCEPTED_REPLAN_REQUIRED decision; create a bounded repair wave and produce proof suitable for ChatWeb final acceptance.
- Objective revision: `4`
- Objective SHA-256: `0ceba55d12cb10aa666b97e8ba4466f65990959cd2471a8a8831b991da0370cc`
- Objective source: `replan_request`
- Mode: `deep_single_lane`
- Base HEAD: `0a9d4c1325624a85f051beabb5a9af88bae9d691`
- Worktree fingerprint: `8af576d61b6d4b8c1faf752f551cc5576a2f76e5bfc91e1e82d7fb4ac2fabbdf`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 77e47efce664439dbce5045c4ceaceed | CODEX:sol_xhigh | sol_xhigh | sol_xhigh | gpt-5.6-sol | xhigh | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28106 | 2026-08-22T19:35:10.015Z | wave_replanned |  | PREFLIGHT | reason=Final acceptance was rejected after review found a bounded WAL/TOCTOU race and missing replacement durability in compact_ledger: a late writer can append to SQLite WAL after preflight while the main DB SHA remains unchanged, allowing os.replace to proceed. Repair only this maintenance boundary and prove it fail-closed without reopening P0/P1/P3. |
| 28107 | 2026-08-22T19:35:11.760Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 28108 | 2026-08-22T19:35:11.942Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 28109 | 2026-08-22T19:35:12.105Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28110 | 2026-08-22T19:35:12.291Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28111 | 2026-08-22T19:35:12.516Z | route_selected | READY | READY | reason=explicit_request; requested=sol_xhigh; resolved=sol_xhigh |
| 28112 | 2026-08-22T19:35:12.741Z | state_transition | READY | ROUTED | reason=route_selected |
| 28113 | 2026-08-22T19:35:13.045Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:sol_xhigh |
| 28114 | 2026-08-22T19:35:13.233Z | model_dispatch_started | ROUTED | ROUTED |  |
| 28115 | 2026-08-22T19:35:13.394Z | model_dispatch_finished | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE; status=error |
| 28116 | 2026-08-22T19:35:13.636Z | delegation_finished | ROUTED | ROUTED | reason=PROMPT_TOO_LARGE; status=blocked |
| 28117 | 2026-08-22T19:35:13.769Z | failure_observed | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE |
| 28118 | 2026-08-22T19:35:13.907Z | state_transition | ROUTED | REPLAN | reason=PROMPT_TOO_LARGE; failure_class=PROMPT_TOO_LARGE |
| 28119 | 2026-08-22T19:35:14.105Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Chain head: `c95e9f790aec35f5d7ca5d562da47fad74065c22f8fb193b08e7a7e687efcf67`
