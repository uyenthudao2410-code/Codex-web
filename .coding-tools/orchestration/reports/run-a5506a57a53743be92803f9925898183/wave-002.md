# Orchestration Wave 2

- Run: `a5506a57a53743be92803f9925898183`
- Wave: `10e0b826c09f4d89acc322395072d9e2`
- Objective: Map the P0.3 F1-F9 Recovery fault matrix on exact delivered HEAD 885260b404c2c64df1b1afa835963045ac55dbf6 before any new mutation. For each F1-F9 in docs/PRODUCTION_CLOSURE_ROLLOUT.md, identify exact existing test names/functions/scripts and whether they are deterministic/unit, current-process integration, or isolated packaged real-process evidence. Reuse exact current coverage where it already proves the required behavior. Identify the smallest genuine gaps only. Pay special attention to whether F2 Recovery Host crash + installed Supervisor restart is covered in a real installed/isolated process harness, and whether F3-F6 subordinate owned-process exits are covered with new PID, preserved unaffected peer, exact port/device identity and no duplicate listener. F7/F8/F9 may be deterministic if they fully prove ownership/backoff invariants. Never propose killing the active development Coding MCP/Recovery Host/Tunnels. Return a concrete matrix with exact commands to run and minimal files to change only if needed.
- Mode: `deep_single_lane`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `5d82026f8a9bc78da6473002cd51239f92a30b235ad850d5c7c5f1f0d64709c5`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 22daf1d6a352406498d40626e427e8a3 | CODEX:terra | terra | terra | gpt-5.6-terra | high | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13178 | 2026-08-17T09:25:36.434Z | wave_replanned |  | PREFLIGHT | reason=Previous deterministic wave only verified the unchanged baseline and modified zero application files. Replan to an implementation-capable Terra deep single lane that must inspect and edit the renderer UI before verification. |
| 13179 | 2026-08-17T09:25:37.483Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13180 | 2026-08-17T09:25:37.647Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13181 | 2026-08-17T09:25:37.838Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13182 | 2026-08-17T09:25:38.071Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13183 | 2026-08-17T09:25:38.247Z | route_selected | READY | READY | reason=explicit_request; requested=terra; resolved=terra |
| 13184 | 2026-08-17T09:25:38.456Z | state_transition | READY | ROUTED | reason=route_selected |
| 13185 | 2026-08-17T09:25:39.049Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:terra |
| 13186 | 2026-08-17T09:25:39.295Z | model_dispatch_started | ROUTED | ROUTED |  |
| 13187 | 2026-08-17T09:25:40.929Z | model_dispatch_finished | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE; status=error |
| 13188 | 2026-08-17T09:25:41.284Z | delegation_finished | ROUTED | ROUTED | reason=PROMPT_TOO_LARGE; status=blocked |
| 13189 | 2026-08-17T09:25:41.538Z | failure_observed | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE |
| 13190 | 2026-08-17T09:25:41.723Z | state_transition | ROUTED | REPLAN | reason=PROMPT_TOO_LARGE; failure_class=PROMPT_TOO_LARGE |
| 13191 | 2026-08-17T09:25:41.964Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `80`
- Chain head: `05b19844e5ace548d94c537611d1f18768f4cbb6596c4721e8b617683fff351d`
