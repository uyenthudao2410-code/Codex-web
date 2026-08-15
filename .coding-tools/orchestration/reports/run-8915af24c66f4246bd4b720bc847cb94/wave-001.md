# Orchestration Wave 1

- Run: `8915af24c66f4246bd4b720bc847cb94`
- Wave: `c93e4b93c4cd458b939bfa8def0752ca`
- Objective: Harden only the internal Code Mode project-relative path contract against Windows namespace aliases that can bypass ordinary repository-file expectations without leaving the lexical project path. Reject ':' anywhere in a Code Mode path to block drive/URI/NTFS alternate-data-stream syntax, and reject Windows reserved device basenames (CON, PRN, AUX, NUL, COM1-COM9, LPT1-LPT9, case-insensitive, including extensions) in any path component. Preserve existing absolute/UNC/~/'..'/NUL/symlink/root fences and all normal Runtime file behavior outside Code Mode. Add focused negative tests. Keep Code Mode disabled/gated and Smart-v3 unchanged. No restart, deploy, commit, push, provider call, or routing change.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `700cf7e699eb993c5ac957a164160cd382a6f70fe9878af28f1afa1c00214acf`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4087 | 2026-08-15T03:28:23.758Z | run_started |  | PREFLIGHT |  |
| 4088 | 2026-08-15T03:28:23.937Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4089 | 2026-08-15T03:28:24.152Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4090 | 2026-08-15T03:28:24.329Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4091 | 2026-08-15T03:28:24.536Z | state_transition | READY | ROUTED | reason=route_selected |
| 4092 | 2026-08-15T03:28:25.116Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4c7d4b5a336f4799909c04fe3470c8fd |
| 4093 | 2026-08-15T03:28:25.301Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4094 | 2026-08-15T03:28:25.928Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4c7d4b5a336f4799909c04fe3470c8fd |
| 4095 | 2026-08-15T03:28:26.122Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4096 | 2026-08-15T03:28:26.574Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ad92f28ccdff5d4d; input_fingerprint=2c0be0618d42fee25a16f9113f743b807bfd93b334bd03af1e44df4ebec5e58b |
| 4097 | 2026-08-15T03:28:27.060Z | proof_recorded |  |  | stage_id=check:ad92f28ccdff5d4d; status=passed; cache_hit=False; input_fingerprint=2c0be0618d42fee25a16f9113f743b807bfd93b334bd03af1e44df4ebec5e58b |
| 4098 | 2026-08-15T03:28:27.284Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=151b061f409fe5c853288e30b004e28adc0233a5749df37e14b1f7790730d6da |
| 4099 | 2026-08-15T03:28:27.985Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=151b061f409fe5c853288e30b004e28adc0233a5749df37e14b1f7790730d6da |
| 4100 | 2026-08-15T03:28:28.170Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a2d1144b214313b7e1bf8004b884fabf27478474296f4af576f2bed387b86549 |
| 4101 | 2026-08-15T03:28:30.426Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=a2d1144b214313b7e1bf8004b884fabf27478474296f4af576f2bed387b86549 |
| 4102 | 2026-08-15T03:28:31.047Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4103 | 2026-08-15T03:28:41.582Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ad92f28ccdff5d4d | passed | 2c0be0618d42fee25a16f9113f743b807bfd93b334bd03af1e44df4ebec5e58b | False | 176 | 0 |
| check:466c2f308b48c766 | passed | 151b061f409fe5c853288e30b004e28adc0233a5749df37e14b1f7790730d6da | False | 320 | 0 |
| verify:tests | passed | a2d1144b214313b7e1bf8004b884fabf27478474296f4af576f2bed387b86549 | False | 1921 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 052a0fe9d4f644c68e5b82292c8f24e8 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 4f98c07f574f06f1d3794885c8bd3ab74529adc4b1f82d27d79b083d3e0e3ec0 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `17`
- Chain head: `64c5cad7619469eca73af30203c55140b5c645f776db6e563e6990ef18fa3f7a`
