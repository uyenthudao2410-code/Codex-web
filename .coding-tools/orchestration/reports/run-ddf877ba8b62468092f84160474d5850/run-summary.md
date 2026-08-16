# Orchestration Run Summary

- Run: `ddf877ba8b62468092f84160474d5850`
- Task: `6a7afa3c9c9b4829b5425c0e81e63728`
- Objective: Fix the accepted-code auto-activation BASE_HEAD_CHANGED deadlock exposed during Phase 3 deployment. Current controller stores one global baseline.head and throws before discovering a newly accepted checkpoint when Git HEAD has advanced. Replace that with a backward-compatible per-component baseline-head transition: each component baseline row tracks its own head (falling back to legacy baseline.head); when target HEAD differs, compute bounded Git name-only delta from that component's baseline head to current HEAD, union those paths with forced dirty/untracked component paths, and require each current byte to match either the component running-baseline receipt or a canonical accepted receipt on current HEAD. Never recapture changed bytes merely because running_revision==disk_revision. A component may advance its baseline head/revision only after a completed/ALREADY_CURRENT intent whose final revalidation trusted the current HEAD. Components whose bytes/revision are provably unchanged may advance their row head automatically. Keep legacy version-2 state compatible and fail closed on missing/invalid base commit, oversized delta, unaccepted committed changes, or concurrent active intent. Add deterministic regressions for: accepted checkpoint on new HEAD can activate; committed head delta without receipt blocks; already-current externally loaded accepted bytes can safely advance; one component can advance while another remains on old head; and legacy baseline state migrates without trusting new bytes. Preserve Phase 3B source and deployed external supervisor.
- Status: **accepted**
- Started: `2026-08-16T09:18:52.667Z`
- Finished: `2026-08-16T09:44:49.595Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `370d597364294cc3a0c94b9e40f87554` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 2 | `83a6d3581d4346219bae76ecd0f6621f` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f9e1a3153091460e87bb133b88760e14 | 83a6d3581d4346219bae76ecd0f6621f | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 84083fd0d91ff3a4a5e3d7de1a9f327a84f9a64674cbacb752fd88fc70a49e50 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 6776 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6803 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 6797 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `5d67bb76ec16b35e70c723aedb0fca495ce9efc834658c171df14383e8beefbf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
