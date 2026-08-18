# Orchestration Wave 1

- Run: `c9a9b60b593e45af885abb93a0bb257c`
- Wave: `8aa14021beb646208f3d475504066954`
- Objective: Continue the existing read-only P3 pilot preflight. Inspect only the runtime compute-placement implementation and current connected execution capabilities needed to enact a valid A/B pair. Determine exactly how LOCAL_FIRST_V1 can be held local and how SERVER_FIRST_DETERMINISTIC_V1 can force or prove remote/server compute for the same deterministic Cargo validation. Identify whether a currently connected distinct server-compute target exists, and whether source snapshot/exact-source requirements are satisfied. Do not modify source, do not run treatment, do not create a representative evaluation row. Return the concrete tool/action sequence and any blocker.
- Mode: `mcp_only`
- Base HEAD: `bc17700e475ce74c96a9547117aade58823f0811`
- Worktree fingerprint: `e8c159440c324c40eb2c8f2f3d85416a377d64be6d5c466ea3d0bd1089609264`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15935 | 2026-08-17T23:36:53.499Z | run_started |  | PREFLIGHT |  |
| 15936 | 2026-08-17T23:36:58.617Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15937 | 2026-08-17T23:40:53.312Z | state_transition | PREFLIGHT | ABORTED | reason=Read-only P3 preflight complete. Representative pair not enrolled: current controller evaluation.policy is metadata-only and explicitly grants no routing authority; runtime cargo auto-offload constructs ServerPreferred for eligible heavy validation, while LocalOnly has no executable selector on the same request. Running A/B now would violate vary_only=compute_placement because local baseline would require changing timeout/sandbox/target availability/environment. No source files were modified and no representative evaluation row was created. |
| 15938 | 2026-08-17T23:40:53.590Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `4`
- Chain head: `b1ac44411c0008c2d9537025a442c127e9e5c40812bb988986c6bfa50df85c9e`
