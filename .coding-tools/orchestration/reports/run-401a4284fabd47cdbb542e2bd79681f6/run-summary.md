# Orchestration Run Summary

- Run: `401a4284fabd47cdbb542e2bd79681f6`
- Task: `c576edd649cb45979d96fe8a19e7d614`
- Objective: C01/M02 machine-A candidate replacement step for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Replace only the stale persistent acceptance installation at %LOCALAPPDATA%\WebMcpAcceptance-1.0.0 with the already-checkpointed fresh NSIS artifact dist\coding-tools-mcp-setup-1.0.0.exe whose exact SHA256 is a2b6fe2d168af983e5a21c461453593f71be3b5609d14172b770fb5d3155d887 and size is 121749108. Before mutation, prove the installer identity and prove the existing acceptance installation is stale. Perform a bounded silent uninstall/reinstall only for that acceptance root, then verify installed Coding Tools MCP.exe SHA256 exactly cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c, installed recovery-supervisor.ps1 SHA256 exactly 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab, launcher SHA256 exactly 082d4b2a8c5cc40a76b778c8503f29c6985edc3e8b3f6d688a205416e9b23a90, and exactly one matching uninstall registration. Prove the currently running production Recovery Host identity and Recovery Supervisor manifest/task are unchanged across this candidate replacement. Do not change production Recovery Supervisor mode yet. Do not reboot/logoff/restart runtime, edit repository source, commit, push, release, publish, or deploy. If any postcondition fails, rollback to a clean acceptance installation state without touching the production Recovery Supervisor.
- Status: **accepted**
- Started: `2026-09-15T08:58:18.319Z`
- Finished: `2026-09-15T09:02:08.646Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `cc6d939a32f94c28a6f9bdc811c1eb05` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ba25cde4ba744c0bb7595aab65ae4bec | cc6d939a32f94c28a6f9bdc811c1eb05 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 00743f546ee49f4a7eecb2fd832572bb53585199ccd7473d4f6a4d163d9b835b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 58671 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `bf0ee871cc2bb1b160c7a20aceb54bd1184fa5150024b301810992da4912b808`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
