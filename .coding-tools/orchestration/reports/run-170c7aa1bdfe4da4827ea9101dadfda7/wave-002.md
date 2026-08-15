# Orchestration Wave 2

- Run: `170c7aa1bdfe4da4827ea9101dadfda7`
- Wave: `ef2a385de5a8458797af720bf49bf2b3`
- Objective: P1C inspect the existing Windows build/package/install-smoke path and identify the smallest exact-source provenance insertion point. Required identity: exact Git SHA plus clean/source fingerprint, app version, Coding Tools MCP version/build identity, native artifact SHA-256 values, the actual npm/installer candidate SHA-256, and canonical proof identity. The smoke-tested candidate bytes must be the provenance-described bytes. Do not mutate in prepare and do not publish/release/tag/push.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `53b8481afed6c63d58cbcce45049ba07a1cfe692b99547f606a4902867bd66e5`
- Contract fingerprint: `56e43a1eca5142b7c5f20eaa1f3002e0c6193c6d8813ac183f0460eba8748b9d`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3840 | 2026-08-15T02:33:31.696Z | wave_replanned |  | PREFLIGHT | reason=The first proof stopped in the Node validator before reaching PowerShell parsing. The local invariant helper named assert intentionally shadows node:assert, but one line incorrectly called assert.deepStrictEqual. Replace that one key-set comparison with a deterministic JSON equality invariant; keep the provenance contract and all other source unchanged. |
| 3841 | 2026-08-15T02:33:31.866Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3842 | 2026-08-15T02:33:32.020Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3843 | 2026-08-15T02:33:32.136Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3844 | 2026-08-15T02:33:32.298Z | state_transition | READY | ROUTED | reason=route_selected |
| 3845 | 2026-08-15T02:33:32.701Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e3ea93096c90409d940c7be907c36424 |
| 3846 | 2026-08-15T02:33:33.025Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3847 | 2026-08-15T02:33:33.593Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e3ea93096c90409d940c7be907c36424 |
| 3848 | 2026-08-15T02:33:33.740Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3849 | 2026-08-15T02:33:34.126Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=18c80ea758965c4fb7110bc8445f496b783119e58435760cf1c156ad9c55fb24 |
| 3850 | 2026-08-15T02:33:35.013Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=18c80ea758965c4fb7110bc8445f496b783119e58435760cf1c156ad9c55fb24 |
| 3851 | 2026-08-15T02:33:35.506Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3852 | 2026-08-15T02:35:02.927Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 18c80ea758965c4fb7110bc8445f496b783119e58435760cf1c156ad9c55fb24 | False | 594 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 207332b11a064acc9cbfe517d17a45f2 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 6db36ca46cb055b4cc116365fd1088d419b8267ac3c032b4d232db6dac396c20 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `3e031afd248135cd62d49908953ac61389ac44f7f441bece70a4f7e20391781c`
