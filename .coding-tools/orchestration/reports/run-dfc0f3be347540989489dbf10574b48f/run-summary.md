# Orchestration Run Summary

- Run: `dfc0f3be347540989489dbf10574b48f`
- Task: `fef5ae094fc048f090a3cdd79a1ce46f`
- Objective: Perform only the controlled fresh acceptance installation step for P0.2. Preconditions: exact HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, exact installer SHA-256 0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879, Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6, no Recovery Supervisor task/root. The stale %LOCALAPPDATA%\WebMcpAcceptance-0.3.4 root may be removed only if it is still empty and has no process under it. Install fresh package there, verify installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420, then close only any app processes launched from that acceptance root. Do not register the Scheduled Task yet and do not touch development runtime owners.
- Status: **accepted**
- Started: `2026-08-17T08:46:02.690Z`
- Finished: `2026-08-17T08:46:36.712Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `9406a7adde4b4fadb459237cd6fba1ce` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| de0d75ace1e84bf680fd40299f78efb3 | 9406a7adde4b4fadb459237cd6fba1ce | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | d301b82c83cf07bd44b5a54ed570c502dd174bd8ae81d1162e52008f597e99dd | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 12739 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `f256410ae7978cbb267a2240fbd05d665a2678ed35c470d907288804f7fdb55a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
