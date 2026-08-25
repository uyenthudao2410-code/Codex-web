# Production Closure & Orchestration Rollout Control Plan

> Status date: 2026-08-21
> Baseline HEAD at plan start: `3059b218989fda8ebf217d121cd6e8f74a71587d`
> Current delivered HEAD before sparse-state remediation delivery: `d5d4bbb533b21937041c1b48a2005583f2652383`
> Current product: `coding-tools-mcp 1.0.0`
> Historical release baseline used by the evidence below: `web-mcp-assistant 0.3.4`
> Control authority: ChatWeb GPT-5.6 Sol
> Deterministic execution/proof authority: Coding Tools MCP / EOCL
> Canonical causal audit: `.coding-tools/orchestration/ledger.sqlite3`

## 1. Purpose

This file is the living implementation-control document for the final production-closure and orchestration-rollout program. It is updated after each material wave with exact evidence, commit, blockers, rollback notes, and next action. It is not a replacement for the EOCL ledger or generated run/wave reports.

The goal is to finish the current product without adding unnecessary architecture:

1. close repository/runtime-evidence hygiene;
2. prove installed Windows current-session and persistence recovery behavior;
3. prove Recovery fault handling with exact ownership/orphan checks;
4. establish an exact-fingerprint release-candidate gate;
5. collect representative paired routing economics from real accepted tasks;
6. promote only evidence-qualified automatic routes, otherwise remain fail-closed deterministic;
7. evaluate semantic localization/LSP integration only if measured benefit justifies the operational cost.

## 2. Safety and evidence invariants

- No two peer Coding Tools runtimes may independently own the same workspace/ledger.
- `execution_route=auto` remains deterministic until representative accepted paired evidence clears the runtime promotion gate.
- No synthetic/benchmark row can promote production routing.
- No paid provider canary may run without explicit external-cost authorization.
- Installed Windows/Scheduled Task/fault injection steps must verify exact target, current owner identity, rollback path, and quiescent EOCL/managed jobs before mutation.
- Recovery faults must never kill or adopt a foreign/unverified process.
- The complete `.coding-tools/**` tree is project history/evidence and must remain visible to Git and be included in project-state delivery commits/pushes except for the explicitly approved transient SQLite sidecars `.coding-tools/orchestration/ledger.sqlite3-shm` and `.coding-tools/orchestration/ledger.sqlite3-wal`. The canonical `ledger.sqlite3`, host-turn correlation files, projections, reports, logs, backups, and future telemetry artifacts remain versioned.
- No `.coding-tools` path may be treated as a Git/runtime-only exclusion without an explicit user instruction naming that exception. Automation worktrees/nested repositories must live outside `.coding-tools` so individual evidence files remain versionable.
- Source proof, live activation, packaged proof, installed-session proof, and release/publish claims are separate states.
- A green test is not final EOCL acceptance until the relevant wave reaches `CHECKPOINTED` when EOCL acceptance is available and required.
- Wrapper/orchestration projection errors are recorded separately from the underlying terminal command result; neither is allowed to overwrite the other.
- Once source bytes change, every previously built installer/package is stale for final acceptance even if it was valid for the prior exact HEAD.
- True reboot/logon persistence is not inferred from current-session proof. If the active control topology cannot survive logout/reboot and verify the result, it remains an explicit external acceptance item.

## 3. Program status

| ID | Priority | Workstream | Status | Completion gate |
|---|---|---|---|---|
| W1 | Closure | Sparse model-facing results | **ACCEPTED / CHECKPOINTED** | focused proof `19b125e7316942c0b200d52063b031af` green and EOCL accepted |
| W2A | Closure | Bounded artifact import / streaming | **ACCEPTED / CHECKPOINTED** | bounded import/upload contract, streaming proof, integrity/hash guards, accepted run/wave |
| S2 | Closure | Artifact/resource closeout | **ACCEPTED / CHECKPOINTED** | typed provenance wired into real artifact/resource paths, bounded reads, native-image integrity, final focused proof matrix accepted |
| S3 / W4 | Closure | Semantic health + Semantic Repository Graph MVP | **ACCEPTED / CHECKPOINTED (PROVIDER-DEGRADED)** | internal bounded read-only graph accepted with safe text fallback; native semantic provider remains `NATIVE_LSP_BINDING_NOT_CONFIGURED` and is not claimed live |
| S4 / W5 | Closure | Context Compiler + paired efficacy gate | **ACCEPTED / CHECKPOINTED — KEEP_SHADOW / NO_PROMOTION** | deterministic internal compiler accepted; real-ledger evaluation has zero comparable representative treatment pairs, so auto-injection remains unavailable |
| S5 / W6 | Closure | Single-Checkout Mutation Coordinator | **ACCEPTED / CHECKPOINTED — TERMINAL COMPLETED** | existing EOCL/SQLite write-fence authority hardened with session/source/dirty/path fences; focused 19/19 acceptance green; no duplicate coordinator/worktree authority introduced |
| P0.1 | P0 | Repository/runtime-evidence hygiene | **COMPLETE / RETENTION POLICY UPDATED** | all `.coding-tools` paths visible to Git; repository guard present; no nested gitlink evidence substitute |
| P0.2 | P0 | Installed Windows Recovery Supervisor acceptance | **CURRENT-SESSION COMPLETE / PERSISTENCE EXTERNAL** | exact installer + real Scheduled Task + `Action Once` + rollback proven; reboot/logon persistence explicitly remains external/unverified |
| P0.3 | P0 | Production Recovery fault matrix | PENDING | controlled isolated/installed fault cases pass with no foreign adoption, duplicate owner/listener, orphan, or state corruption |
| P1.1 | P1 | Exact-fingerprint release candidate | PENDING | source + MCP + Recovery E2E + packaged + installer/provenance gates pass on one exact accepted fingerprint |
| P1.2 | P1 | Representative routing economics | PENDING | homogeneous accepted paired cohorts by task class/oracle/environment with measured quality/time/cost |
| P1.3 | P1 | Selective auto-routing promotion | GATED | only task classes that satisfy representative promotion thresholds may change from deterministic |
| P2.1 | P2 | Semantic localization optimization | **BLOCKED_CONFIG / ASSESSMENT PENDING** | configure only if exact binding exists and benchmark shows material value; otherwise keep bounded text fallback |
| D1 | Delivery | Commit/push accepted waves | ACTIVE | each accepted source/docs wave pushed with ledger and all current evidence except the two named transient SQLite sidecars |

## 4. Current baseline evidence

### 2026-08-21 sparse/artifact closure checkpoint

#### W1 — Sparse model-facing results

- Status: **ACCEPTED / CHECKPOINTED**.
- Focused accepted proof: `19b125e7316942c0b200d52063b031af`.
- No W1 reopening is authorized by later S2 work.

#### W2A — Bounded artifact import / streaming

- Status: **ACCEPTED / CHECKPOINTED**.
- EOCL run: `214411ecb15d4d3a9f24f2be976d40a0`.
- EOCL wave: `cff215da46404f6e82803c6a41b0a25d`.
- Accepted focused proofs:
  - `e5b0cd77cd8e44f89713370646f7b430` — formatting gate;
  - `5f89619deb224728ad4af48791961ee4` — compile/check gate;
  - `aca687b6553340acaf1b268173b72f9c` — chunked body rejected after size limit without `Content-Length`;
  - `0b4f871481d84bb5ba1e67aa7473190e` — large-file import streamed in bounded chunks;
  - `c934ecd75a47447c9967a3f03bfb0156` — source-name fallback when target is omitted.
- Implemented contract includes `/api/artifacts/import` plus upload begin/chunk/finish/abort, approximately 10 MiB import/upload bounds, `expected_bytes`, `expected_sha256`, MIME validation, overwrite policy, and hash guard.
- The final W2A acceptance wave changed only `src/runtime_http/tests/import_http_tests.rs` test-harness decoding; production import semantics were unchanged.

#### S2 — Artifact/resource closeout

- Status: **ACCEPTED / CHECKPOINTED**.
- Existing provenance subsystem was retained rather than replaced. Typed refs in `resources/coding-tools-mcp/coding_tools_mcp/artifact_refs.py` cover `command_output`, `provider_result`, `orchestration_proof`, `handoff_capsule`, and `build_artifact`, with the applicable owner/durability/restart/content-address/hash/locator/retrieval metadata.
- Real producer/resource wiring was confirmed through:
  - `resources/coding-tools-mcp/coding_tools_mcp/opencode_provider.py` for `provider_result`;
  - `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py` for `orchestration_proof` and `handoff_capsule`;
  - build verification/task-state paths for content-addressed `build_artifact`;
  - `resources/coding-tools-mcp/coding_tools_mcp/task_state.py` plus `artifact_refs.py` for retained `command_output`;
  - `src/tool_runtime/files.rs` and `crates/webcodex-runner/src/webcodex_runner/artifacts.rs` for bounded artifact reads and native-image resource retrieval.
- One concrete S2 defect was found and fixed before closeout: EOCL-owned `command_output` refs lost `owner_run`/`owner_wave` after command admission. The minimal accepted patch persists non-empty command ownership, derives lineage from `payload.execution_owner` with persisted-command fallback, and passes owner lineage into `command_output_artifact_ref`; non-EOCL commands remain ownerless.
- Command-output lineage patch acceptance:
  - run `2166c986b3b54cab8804ec8fff87a93b`;
  - wave `165330542f8d4d8f94bc09676600c112`;
  - proof `024374317fe644308171a9c483e29ab8` — non-EOCL/baseline command-output artifact-ref behavior;
  - proof `60d1647c5b124e3f9d293ce71c271f7d` — EOCL owner lineage survives running state and later `command_control` poll/handoff fallback;
  - accepted files: `artifact_refs.py`, `task_state.py`, `test_task_state_and_build.py` only.
- `read_project_artifact` normal response remains bounded by offset/length with 32 KiB default and 64 KiB maximum response length.
- MCP native-image retrieval uses a separate full-image bound (`MAX_MCP_IMAGE_BYTES`), requires a complete read, validates supported reported MIME against magic-sniffed actual bytes, and verifies SHA-256 of decoded bytes against the reported hash before native MCP image framing.
- Final S2 proof-only acceptance:
  - run `3b978ca3ccb840c1aee84bc122b2a4a6`;
  - wave `765f375570f842f28ae5403d1f643378`;
  - `81b347b7a6dc476f902ff786d81a18da` — real `provider_result` snapshot wiring;
  - `42df2ec52cb44dcc8bf113261faa3414` — bounded/content-free orchestration evidence with `orchestration_proof` + `handoff_capsule` refs;
  - `14fa1e73aa9e43f59a3e81c01c59fd22` — content-addressed workspace `build_artifact` ref;
  - `ae76088ca17f442c80946fb735f5dc3c` — bounded `read_project_artifact` routing;
  - `b9d779057d4341f6a7fa098117ce23ba` — complete bounded MCP-image remote read;
  - `72170b7a8ccd451cb32ae56d6cf60f42` — untrusted/spoofed remote MIME rejection;
  - all six final focused proofs passed; final integrity check passed with `checked=99`, head hash `5390ad5c46e8f2b721c12ae13fcbd904760924da26af1508dba28683191b8c51`;
  - no source or documentation files changed in the final proof-only wave.
- The first final-proof invocation failed only because the command environment lacked `resources/coding-tools-mcp` on Python import path (`ModuleNotFoundError: coding_tools_mcp`). It was classified as an oracle-invocation/environment error and replanned from the package root; no product assertion had failed.
- Earlier broad `npm run test` failures (`EPERM` temp cleanup and source-bundle detection of private runtime state) were outside S2 and were explicitly not used as S2 acceptance oracles.
- **S3 gate:** no S3 source mutation occurred before S2 final acceptance. S3 became eligible only after run `3b978ca3ccb840c1aee84bc122b2a4a6` / wave `765f375570f842f28ae5403d1f643378` reached `CHECKPOINTED`.

#### S3 / W4 — Semantic health + Semantic Repository Graph MVP

- Status: **ACCEPTED / CHECKPOINTED (PROVIDER-DEGRADED)**.
- Exact S3 scope and W4 acceptance contract were recovered from `docs/research/260820_CODING_WEB_TECHNICAL_EVALUATION_AND_IMPLEMENTATION_PLAN.md` before mutation. The phase explicitly requires semantic-provider health auditing without weakening origin/credential controls, plus a small read-only Semantic Repository Graph that remains useful under safe text fallback.
- The existing native semantic binding was not modified or bypassed. Current truth remains `NATIVE_LSP_BINDING_NOT_CONFIGURED`, with missing binding origin and credential-file configuration; no native-provider live activation is claimed by this phase.
- New internal graph implementation: `resources/coding-tools-mcp/coding_tools_mcp/semantic_graph.py`.
- The graph adds **no new public tool, endpoint, database, credential path, provider binding, or authority**; smart-v3 remains an 8-tool public MCP surface.
- V1 records are derived incrementally from the semantic/text localization results already produced by `prepare_coding_context` and carry the applicable file/symbol/definition/reference/import/test association, content/source identity, provider/provider-version, confidence, completeness, current/stale metadata.
- Internal bounded APIs are:
  - `resolve_symbols(query, budget)`;
  - `references(symbol_id, budget)`;
  - `related_tests(symbol_id, budget)`;
  - `impact(seed_symbols, depth, budget)`.
- Safety/boundedness properties:
  - only safe project-relative paths are indexed;
  - source identity is SHA-256 bound; small files can use a complete file identity while large files use a bounded prefix/suffix sample and are explicitly `partial` / currentness-uncertain rather than falsely complete;
  - text fallback remains usable but is marked lower-confidence/partial;
  - changed source is marked stale and is never reported current;
  - incremental refresh replaces touched-path records and retains untouched records;
  - each stored record remembers the **exact per-file read budget** used to derive its sampled identity, so stale refresh cannot falsely compare against a different sample window;
  - the in-memory graph has a hard lifetime cap of `MAX_GRAPH_RECORD_BUDGET=200`; oldest derived records are evicted first, and eviction contributes to dropped/partial evidence rather than allowing unbounded accumulation.
- `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py` lazily owns the internal graph and projects only **content-free graph status** into `composite_read.execution.localization.semantic_graph`; existing focused proof confirms raw query/symbol text is not added to the model-facing composite execution metadata.
- Acceptance review deliberately rejected the first two otherwise-green waves before final acceptance:
  1. wave 1 exposed a false-stale bug where later large files could be refreshed with a larger hash sample budget than the one used at indexing time;
  2. wave 2 exposed lifetime accumulation because the record cap initially bounded each update but not the whole in-memory graph.
  Both defects were fixed with discriminating regressions before acceptance; no reset/rollback of the valid S3 work was used.
- Final S3/W4 acceptance:
  - run `c074433369cd42e1b60fb66c21454980`;
  - wave `f02b50c4268b4ee19a0d0dfe794800bd`;
  - proof fingerprint `f84267fcebd2da613d85038f4f7193fd81ed9b29d54c500f86ce8b8b85d15955`;
  - proof `cd100e39667444a89a5a77cc8bcc1661` — semantic graph suite covering degraded fallback, references/tests/impact, stale detection, incremental reuse, bounded sampled hashes, exact reduced-remaining-budget refresh, and 240-record lifetime-cap regression;
  - proof `438ecaec03df482c9e666eb434bdd9ca` — `prepare_coding_context` semantic + text-fallback graph integration and no-query-leakage invariant;
  - proof `eb7f022e05524075a6d998ace55a2db2` — native binding remains defaults-off and fails closed for invalid/unconfigured binding;
  - all three final focused proofs passed;
  - final integrity check passed with `checked=93`, head hash `293e9a9d5ee098ecb501c1144b88e696d2ca8afa4170aa8e9841a0cdd9f7d92e`.
- Accepted file receipts:
  - `resources/coding-tools-mcp/coding_tools_mcp/semantic_graph.py` SHA-256 `2d9167999bd4a3eea808f6aa9ce8483bac497f7a63d8ad4440dde633ec22c0c4`;
  - `resources/coding-tools-mcp/tests/test_semantic_graph.py` SHA-256 `0c01c4e5ba9ef15ed800566cd2617f414e87b76650bdf14a66a0dac499e84d1c`;
  - `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py` SHA-256 `627f2073e77f5abcdadfff6091afec4c565d57fa05c193ac626881345cc92c45`;
  - `resources/coding-tools-mcp/tests/test_task_state_and_build.py` SHA-256 `9cbc910cd406a305cd58742866f35cfa6694371f6e595eb849a65b2810128b67`.
- **Boundary:** S3/W4 acceptance proves the graph layer works safely in provider-degraded/text-fallback mode and preserves semantic binding security. It does **not** prove native LSP activation, and it does not start S4/W5 or any later phase.

#### S4 / W5 — Context Compiler + paired efficacy gate

- Status: **ACCEPTED / CHECKPOINTED — KEEP_SHADOW / NO_PROMOTION**.
- Exact W5 contract was recovered from the maintained technical plan before mutation. The compiler contract is deterministic and receives only supplied evidence: `compile_context(task_intent, repo_revision, token_budget, current_evidence, already_seen, requested_scope)`.
- New internal implementation: `resources/coding-tools-mcp/coding_tools_mcp/context_compiler.py`; focused coverage: `resources/coding-tools-mcp/tests/test_context_compiler.py`; shadow integration remains in `context_tools.py`.
- The compiler adds no public tool/schema/endpoint and does not scan the repository itself. It compiles bounded sections for primary files/symbols, entry points, relations, relevant tests/config/rules, related dirty diff, uncertainty, omitted candidates/reasons, token estimate, completeness, and stable fingerprints.
- Selection semantics are fail-closed: safe scope filtering, file/symbol dedupe, `already_seen` suppression, stale semantic omission, conservative token budgeting, and explicit omitted reasons.
- Treatment gate is `CODING_TOOLS_MCP_CONTEXT_COMPILER` with only `off` and `shadow` accepted. Default is `off`; unsupported values such as `inject` or `auto` fail closed to `off`. There is no auto-injection path in the accepted source.
- `prepare_coding_context` in shadow mode runs the compiler only over evidence already collected by the existing prepare flow, stores the full compiled packet on internal runtime state, and exposes only content-free fingerprint/count/status metadata. Focused proof confirms selected model-facing `files` and `selected_paths` are unchanged between `off` and `shadow`.
- ChatWeb Sol rejected the first otherwise-green source wave because `input_sha256` initially bound only selected/included evidence. The accepted replan binds `input_sha256` to a canonical SHA-256 of the complete supplied `current_evidence`, so even evidence omitted by budget/scope remains audit-bound while `compiled_sha256` continues to describe the actual compiled output.
- Source/MVP acceptance:
  - run `9d1698e4267e4d118144fac810dbe4aa`;
  - wave `1bb808f20b5741be8fd5cd91b0a76a85`;
  - proof fingerprint `7049cefba006b9cc95ddecec466d0cce030fd3b1198c6e436f949f2af64c8381`;
  - proof `a4b9c83e3adb473e9f8eb34c452f60bf` — compiler suite, including budget/dedupe/scope/already-seen, stale/uncertainty, rules/config/diff, stable fingerprints, treatment fail-closed, shadow non-injection, and complete-input fingerprint regression;
  - proof `888c6774db834719a0d9dc7c07e7c2ab` — S3 semantic graph regression;
  - proof `d26113ebdc7a49aca861a9bc94ef83ae` — existing prepare-context semantic/fallback integration regression;
  - integrity after source acceptance: `checked=78`, head hash `9e2721ccdc23bb88355aae2f75e01460e06ff8859ffe2593ec1357f4f688173d`.
- Accepted source file receipts:
  - `resources/coding-tools-mcp/coding_tools_mcp/context_compiler.py` SHA-256 `46094edd29ca54c1268330428cf221cfde91bb07581cb4093d99a76bd3692499`;
  - `resources/coding-tools-mcp/tests/test_context_compiler.py` SHA-256 `358080409230120d68c4bda034cf5c798dfa0061b1340cea226fbc711eca6110`;
  - `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py` SHA-256 `5b5e33a2b5b172c576013252980a4dac685f820555a7425b52d34f8384f170df`.
- The required efficacy gate used the existing model-free ledger evaluator; no new evaluator and no synthetic/benchmark/replay work was created to manufacture evidence.
- Real-ledger evaluation:
  - run `b204662b3c8748bba2bfbe3f02de1ea6`;
  - wave `2165d6ccafb94ef4b5ce05ee6984b18d`;
  - baseline policy `chatweb_mcp` vs candidate `context_compiler_shadow`;
  - thresholds: minimum 10 representative pairs and 4 task classes;
  - real ledger runs observed: `794`;
  - pair-tagged runs scanned: `0`;
  - comparable pair count: `0`;
  - accepted pair count: `0`;
  - task-class count: `0`;
  - evaluator status: `hold`;
  - Pareto status: `indeterminate_no_pairs`;
  - hold reasons: `insufficient_paired_results`, `insufficient_task_class_diversity`;
  - routing-placement regret: `indeterminate_no_comparable_pairs` / `no_comparable_pairs`;
  - total monetary cost: incomplete, reason `controller_cost_unobserved`;
  - `automatic_activation=false`.
- Evaluation proofs:
  - `afbba58874f54b138040b087edc841ff` — real current-ledger evaluation;
  - `545d02d13ba74b10807032585e8fa363` — zero-pair evaluation remains indeterminate/fail-closed;
  - `acdd074415bb4b3395f298c583bd574d` — missing total controller cost remains unknown rather than zero and blocks promotion;
  - proof fingerprint `6555d22e18322e78bfcf1b637ca6bece06b59cabbbceb274ef2124098d48c47b`;
  - final evaluation integrity: `checked=28`, head hash `59c92edd2f339e4fda7505fdee040e04dd88cd1f5687ed01988eea133a72a402`;
  - no files changed in the evaluation wave.
- **Accepted decision:** `KEEP_SHADOW / NO_PROMOTION`. This is a successful fail-closed efficacy decision, not an incomplete implementation. Auto-injection remains unavailable until future representative comparable pairs independently satisfy the W5 efficacy gate.
- **Boundary:** S4/W5 acceptance does not start S5/W6 or authorize mutation-coordinator changes.

#### S5 / W6 — Single-Checkout Mutation Coordinator

- Status: **ACCEPTED / CHECKPOINTED — TERMINAL `COMPLETED`**.
- Exact W6 contract was recovered from `docs/research/260820_CODING_WEB_TECHNICAL_EVALUATION_AND_IMPLEMENTATION_PLAN.md` before S5 mutation. The accepted design deliberately **augments the existing EOCL + durable SQLite workspace write-fence authority** rather than creating a second coordinator, alternate checkout authority, worktree promotion system, or source-owner subsystem.
- Existing authority retained: one global workspace write fence with fencing tokens, EOCL run/wave state, lease expiry/renewal/recovery, terminal revoke, candidate proposal-only profiles, and the smart-v3 public MCP surface.
- Final S5 source/test surface:
  - `resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py`;
  - `resources/coding-tools-mcp/coding_tools_mcp/server.py`;
  - `resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py`;
  - `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py`;
  - `resources/coding-tools-mcp/tests/test_orchestration_control.py`;
  - `resources/coding-tools-mcp/tests/test_efficiency_runtime.py`.
- Final overall S5 source delta: **6 files changed, 379 insertions, 10 deletions**; scoped `git diff --check` passed.
- Mutation lease now audit-binds `owner_session`, `source_fingerprint`, `runtime_worktree_fingerprint`, `protected_paths`, `existing_dirty_source_paths`, `started_at`, and lease `state`, while preserving the existing run/wave/base-head/fencing-token/allowed-path authority.
- Pre-write admission is fail-closed before source mutation and checks:
  - active EOCL/write-fence ownership and lease expiry;
  - execution-context-bound owner session;
  - base/source/runtime fingerprint drift;
  - foreign dirty source paths relative to the lease snapshot;
  - exact requested patch/move/directory paths against allowed scope;
  - protected roots before mutation;
  - candidate-proposed paths again at the MCP authority boundary.
- Typed safety failures include `WRITE_SESSION_MISMATCH`, `FOREIGN_DIRTY_SOURCE`, `SOURCE_DRIFT`, `PROTECTED_PATH_WRITE`, existing `WRITE_SCOPE_VIOLATION`, and candidate-boundary `CANDIDATE_SCOPE_VIOLATION`; violations replan/fail closed rather than reset, restore, rebase, merge, or silently transfer authority.
- Protected-root matching is case-insensitive via `casefold()`, preventing Windows variants such as `.GIT/config` from bypassing the protected-path fence.
- `owner_session` is bound to the Execution Hub client record identity when present, including the execution-context dimension, so reconnect recovery cannot silently duplicate a logical writer session.
- Persisted `write_lease_acquired` events contain the new lease metadata and recovery reconstructs it; terminalization records released state and leaves no active source fence.
- Source identity continues to exclude `.coding-tools` runtime/evidence churn, so ledger/projection activity does not falsely contend with source ownership.
- Candidate/reviewer authority remains proposal/read-only with `checkout_write=False`, `direct_tool_access=False`, `candidate_only=True`, and `authoritative_write=False`; exact patches are still applied only by the MCP-owned source-write path after admission.
- Public surface remains **smart-v3 with exactly 8 tools**; S5 adds no ninth tool, endpoint, provider transport, or hidden mutation bypass.
- Wave 1 was correctly **not accepted**:
  - run `f2bda257239346f089ccf073f38d4790`;
  - wave `485fabde2223430bb42408adcc48b406`;
  - proof `2b4df408c0ea4b539a6098fccfa15c99`;
  - broad focused suite result: **1 failed / 23 passed**;
  - EOCL revoked the write lease and moved to `REPLAN` before further mutation.
- Fresh-wave diagnosis isolated that one failure to an unrelated hard-coded tool-contract SHA assertion in `EfficiencyRuntimeTests::test_tool_contract_metadata_is_stamped_everywhere`: expected historical hash `bd5c6810890b5383da37c234e66c76256727b5b86b2a2b84cad1022939649a5c`, runtime current hash `e94245deec7c7988863275294174c14d2d0d4ec20c2a4eda1ab61e87f77d9114d`. S5 did not modify the public tool-schema/contract files, and this stale assertion was intentionally **not edited merely to manufacture a full-suite green**.
- ChatWeb acceptance review then found and corrected two genuine S5 hardening details before closure: Windows case-folded protected-root matching and execution-context-bound `owner_session`, with a regression for uppercase protected-root bypass.
- Final S5/W6 acceptance:
  - run `f2bda257239346f089ccf073f38d4790`;
  - fresh replan wave `779af9e5182a4fafbec31ac4dfee7521`;
  - focused acceptance result: **19/19 PASS** across orchestration-control, source-identity, smart-surface, and Codex-bridge regressions;
  - proof `657e21d54803457688e85f8d506f2a98`;
  - proof fingerprint `65cfcaf39b87e63221ad873f4e0c1b1c676e531c13f31d42af7f0c7bf47fb2fc`;
  - focused proof bound runtime source fingerprint `7b35c0050e8a9ea0d96748104dea6336376f18c00c88f799f37d9fb01f29ea48`;
  - EOCL audit was clean, the write lease was released, no active workspace fence remained, and the accepted artifact was recorded;
  - explicit ChatWeb accept terminalized the run/wave as `COMPLETED`.
- **Known debt deliberately preserved:** the broad efficiency suite still contains the stale hard-coded tool-contract SHA assertion above. It is not counted as an S5 product regression and is not represented as green in this document.
- **Boundary:** S5/W6 acceptance proves single-checkout mutation ownership/fencing and reconnect-safe source admission using the existing authority. It does not start S6, does not authorize a new trust boundary or provider, and does not imply release/tag/publish. No commit, push, release, tag, or publish was performed for this S5 wave.

### Already closed before this plan

- P2/P3 LSP/resource hardening closed on 2026-08-16 with live Connector/Runner/rust-analyzer soak and fail-closed resource controls.
- Device Identity + Recovery ownership + controlled Recovery activation closed technically and delivered.
- Packaged Recovery Host/Supervisor isolated smoke exists via `npm run test:recovery:packaged`.
- Organic host-turn correlation lifetime race was fixed so pending identity survives until `host_turn_span` finalization.
- Windows live-supervisor E2E cleanup was hardened by waiting for child `close`; broad root Node verification had previously passed.

### Current intentional gates

- Automatic non-deterministic routing: OFF / deterministic fail-closed.
- Auto-handoff: OFF.
- Context Compiler auto-injection: **OFF / unavailable**. Accepted modes are only `off` and `shadow`; S4/W5 result is `KEEP_SHADOW / NO_PROMOTION` because the real ledger has no comparable representative treatment pairs yet.
- Single-checkout source mutation: **one EOCL/SQLite workspace write-fence authority only**. S5/W6 is accepted; session/source/dirty/allowed/protected-path violations fail closed and candidate/reviewer lanes remain no-write.
- Paid OpenCode Flash terminal canary: not authorized by this plan.
- Native semantic localization remains unavailable with `NATIVE_LSP_BINDING_NOT_CONFIGURED`; runtime reports missing binding origin and credential-file configuration. **S3/W4 graph is accepted in provider-degraded/text-fallback mode only** and is not evidence of native semantic-provider live activation.

## 5. P0.1 — Repository/runtime-evidence hygiene

### Historical implementation at `bae11481` (superseded for Git retention)

- Added exact runtime-only ignore rules for:
  - `.coding-tools/evaluation/chatweb-host-turn-pending.json`
  - `.coding-tools/evaluation/chatweb-host-turn-binding.json`
  - `.coding-tools/orchestration/ledger.sqlite3-wal`
  - `.coding-tools/orchestration/ledger.sqlite3-shm`
- Preserved `.coding-tools/orchestration/ledger.sqlite3` as a tracked canonical evidence file.
- Preserved live one-shot binding state on disk while removing it from source-control concerns.
- Removed the accidentally tracked pending-turn snapshot from source control.

### Current retention policy — 2026-08-18 named sidecar exception

- Current operator direction requires **all files under `.coding-tools/**` to be committed/pushed as historical evidence except exactly** `.coding-tools/orchestration/ledger.sqlite3-shm` and `.coding-tools/orchestration/ledger.sqlite3-wal`.
- `.gitignore` must keep those two transient SQLite sidecars ignored/untracked while keeping `ledger.sqlite3`, host-turn correlation files, runtime projections, reports, logs, backups, and all other `.coding-tools` evidence visible to Git.
- Before commit/push, stage the deliverable tree with `git add -A -- .coding-tools` and require `npm run check:coding-tools-delivery` to pass; the guard must reject any broader `.coding-tools` ignore exception.
- The historical bullets above remain only as chronology of what `bae11481` and the 2026-08-17 full-retention policy did; they must not be used as authority to re-add the two transient sidecars or omit any other current `.coding-tools` evidence.

### Proof and delivery

EOCL run `4755a66728bf42ed92e2692d15212391`, wave `0f2ce962fa8b4dcdbb1e1087cfcad7e7` reached `CHECKPOINTED`.

Passed:

- exact `git check-ignore -v --no-index` for all four runtime-only paths;
- canonical ledger `git ls-files` tracking proof;
- `node scripts/check-source-root-clean.js` -> `source root clean`;
- scoped `git diff --check`.

Delivered commit:

- `bae11481 chore: close runtime evidence hygiene`
- pushed to `origin/main`.

## 6. P0.2 — Installed Windows Recovery Supervisor acceptance

### 6.1 First installed acceptance attempt — FAILED AS DESIGNED

Exact delivered source used for the first installer attempt:

- HEAD: `bae11481a54c5ec9ecd2c724b15ee2e4539e3bdf`
- version: `0.3.4`
- NSIS installer: `dist/web-mcp-assistant-setup-0.3.4.exe`
- installer size: `128661526` bytes
- installer SHA-256: `66a2455bfed8c9b8da4b1d755b1c27513ef04285e8412a761334734b3b455481`

Preflight proved there was no existing acceptance installation and no existing `WebMCP Recovery Supervisor` Scheduled Task. Development primary/recovery planes were alive and were not modified by the installation step.

The installer was installed silently into a controlled per-user acceptance location. The Scheduled Task was created with the expected same-user Limited principal, logon + minute heartbeat triggers, fixed PowerShell action, packaged manifest, fixed `--recovery-host` argv, and executable hash. However its runtime acceptance failed:

- Task state: `Ready`
- `LastTaskResult = 1`
- installed supervisor `Action Once` returned `RECOVERY_SUPERVISOR_FAILED`
- message: `Recovery Supervisor executable missing.`

The manifest itself contained the correct Unicode executable path and independent filesystem proof showed the executable existed. The root cause was packaged-source drift:

- current source Recovery Supervisor SHA-256 at diagnosis: `540730e485fb6ddf802c6df5be1a638fa920d4d1531144a8d6bb75d4fc42090f`
- packaged/installed Recovery Supervisor SHA-256: `7c2e89822a78b647e6d979a9dc052da6c404172bb5527f90380feb121f2d9ca8`
- current source contained explicit UTF-8 file-reading handling;
- packaged copy did not.

Therefore the installer was not byte-identical to current `resources/` and the installed Unicode-path test correctly exposed the stale package.

Rollback was executed immediately:

- `WebMCP Recovery Supervisor` unregistered successfully;
- task presence after rollback: false;
- persistent app settings/secrets/runtime state and project ledger were not deleted.

### 6.2 Packaging integrity remediation — COMPLETE / DELIVERED

Implemented:

1. `scripts/clean-dist.js` removes `dist/` with bounded Windows retries before every Electron Builder package.
2. `package.json` routes both `dist` and `dist:dir` through the clean step.
3. `scripts/verify-packaged-resources.js` builds an allowed source/package file projection and fails closed on missing, unexpected, size-different, or SHA-256-different packaged resources while preserving cache/runtime/report exclusions.
4. `scripts/packaged-recovery-smoke.js` checks that the packaged Recovery Supervisor hash equals current source before spawning packaged processes.
5. `tests/build-verification.test.js` covers the clean-output requirement and stale packaged-byte rejection.

Proof:

- standalone `npm run test:recovery:packaged` terminal run exited `0` after Electron Builder packaging;
- packaged Recovery smoke returned `ok=true`;
- Recovery Host/device/recovery MCP/Supervisor/fail-closed guards passed;
- focused `build-verification + recovery-supervisor` tests: **13/13 PASS**;
- full allowed resource source/package identity: `exact_source=true`, **249 files**;
- scoped/global diff hygiene passed.

EOCL acceptance for the packaging remediation reached a clean checkpoint before delivery.

Delivered commit:

- `d5d4bbb5 fix: enforce exact-source packaged resources`
- pushed to `origin/main`.

### 6.3 Fresh exact-HEAD installer from packaging-hardened source — BUILD ACCEPTED

EOCL build run:

- run: `3ca4f890a8ae4090ac9858c0b0e68d46`
- wave: `16b3281053d24c32941153b9ab1fc428`
- final state: `CHECKPOINTED`

Exact source/artifact:

- HEAD: `d5d4bbb533b21937041c1b48a2005583f2652383`
- version: `0.3.4`
- `npm run dist`: exit `0`
- installer: `dist/web-mcp-assistant-setup-0.3.4.exe`
- installer size: `128670087` bytes
- installer SHA-256: `A81AAB1C1399F4E8D57E090CBA25E5B6A939EDE2F9EB60E9C2C8A8E10C723AE2`
- packaged Recovery Supervisor SHA-256: `540730E485FB6DDF802C6DF5BE1A638FA920D4D1531144A8D6BB75D4FC42090F`

The packaged supervisor was byte-identical to the source for that exact HEAD. This installer was valid for the second installed acceptance attempt, but became stale for final acceptance once the sparse-state source remediation below changed supervisor bytes.

### 6.4 Second installed acceptance attempt — FAILED AS DESIGNED ON PERSISTED-STATE COMPATIBILITY

Preflight immediately before mutation proved:

- exact HEAD `d5d4bbb533b21937041c1b48a2005583f2652383`;
- installer SHA/size exactly matched the accepted build above;
- controlled acceptance installation `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4` was absent;
- Scheduled Task `WebMCP Recovery Supervisor` was absent;
- supervisor install root was absent;
- persisted supervisor status existed in the sparse `uninstalled` shape created by prior uninstall;
- Recovery Host descriptor owner PID `32536`, instance `f021dea5f56a9e72b7cce8b59908c003`;
- primary MCP listener: port `18766`, PID `24420`;
- Recovery MCP listener: port `18767`, PID `38980`;
- primary Tunnel listener: health port `18082`, PID `24932`;
- Recovery Tunnel listener: health port `18083`, PID `29972`.

The accepted NSIS installer was installed silently into `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4`:

- NSIS exit: `0`;
- installed executable SHA-256: `37A63DC1BBA170353D0E0355ADCC4FF44D06179532547C66CACC610613BA5DFB`;
- installed Recovery Supervisor SHA-256: `540730E485FB6DDF802C6DF5BE1A638FA920D4D1531144A8D6BB75D4FC42090F`;
- installed `app.asar` SHA-256: `0918156F6AAA6CC2F296ACE30D82818F899DEA8194FBBEC9610AA8DEE4D95574`;
- uninstaller present.

Real Scheduled Task registration succeeded structurally:

- task name: `WebMCP Recovery Supervisor`;
- same-user Interactive logon;
- Limited run level;
- fixed PowerShell action invoking installed supervisor with `-Action Run`;
- logon + minute heartbeat triggers;
- packaged manifest arguments exactly `['--recovery-host']`;
- installed supervisor copy hash matched package/source for `d5d4bbb5`.

Runtime acceptance then failed:

- Task state after launch: `Ready`;
- `LastTaskResult = 1`;
- persisted status still `uninstalled`;
- direct installed `Action Once` exited `1`;
- typed code: `RECOVERY_SUPERVISOR_FAILED`;
- exact error: `The property 'last_healthy_at' cannot be found on this object. Verify that the property exists.`

Root cause:

- the script runs with `Set-StrictMode -Version Latest`;
- `Uninstall` intentionally writes a sparse persisted `uninstalled` status;
- `New-State` directly dereferenced optional historical properties such as `last_healthy_at` that are absent in that sparse schema;
- therefore a legitimate persisted state created by the product itself could not be rehydrated on the next install/run.

This is a real persisted-state schema-compatibility bug. It is independent from the first Unicode/packaging blocker.

Rollback was executed immediately and verified:

- Scheduled Task absent;
- `%LOCALAPPDATA%\WebMcpRecoverySupervisor` absent;
- persisted supervisor status returned to `uninstalled`;
- primary/recovery runtime ownership was not intentionally modified.

The acceptance application itself remains installed only as a stale controlled comparison artifact until replacement by the next exact-HEAD installer.

### 6.5 Sparse persisted-state compatibility remediation — COMPLETE / DELIVERED

Implementation is deliberately minimal:

- added a bounded optional-property accessor used only while materializing `New-State` from persisted JSON;
- missing optional legacy/sparse fields receive safe defaults;
- present malformed values still pass through existing casts/logic and therefore retain existing fail-closed behavior;
- ownership verification, manifest/executable identity, restart thresholds, cooldowns, suppression, mutex handling, and live-owner rules are unchanged.

Normalized optional fields:

- `last_healthy_at`;
- `last_host_pid`;
- `last_host_instance_id`;
- `consecutive_failures` -> default `0`;
- `restart_attempts` -> default empty list;
- `next_attempt_after`;
- `suppressed_until`.

Regression added:

- writes the exact sparse persisted `uninstalled` status shape;
- presents an authenticated healthy Recovery Host with exact PID/instance identity;
- runs `Action Once`;
- requires `healthy`, same host PID/instance, zero consecutive failures, empty restart attempts, populated `last_healthy_at`, and no spawned replacement PID.

Proof:

- `node --test tests/recovery-supervisor.test.js`: **12/12 PASS**;
- `git diff --check -- resources/recovery-supervisor/recovery-supervisor.ps1 tests/recovery-supervisor.test.js`: PASS;
- current remediated supervisor source SHA-256: `E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420`;
- source delta: 2 files, 3 insertions, 1 deletion.

EOCL acceptance:

- run: `274bd626bfb44943afedb3e755002ad0`;
- wave: `62183559c12943ec8e9a9dec25c4f257`;
- final state: `CHECKPOINTED`;
- integrity check: PASS (`checked=76`).

Delivered commit:

- `acaa3582 fix: normalize recovery supervisor persisted state`
- pushed/aligned with `origin/main` before the final P0.2 installer build.

The old `A81A...` installer is intentionally retained as **STALE HISTORICAL EVIDENCE ONLY** because its supervisor bytes predate this remediation.

### 6.6 Final exact-HEAD installed acceptance — CURRENT-SESSION COMPLETE

Exact source/artifact used for final current-session acceptance:

- HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`;
- installer: `dist/web-mcp-assistant-setup-0.3.4.exe`;
- installer size: `128670108` bytes;
- installer SHA-256: `0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879`;
- Recovery Supervisor source/package SHA-256: `E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420`;
- exact packaged resource projection: `249` files, `exact_source=true`;
- accepted build run `c6235e7dfefe4df9938bf6d0b4c11bca`, wave `b344e00d5ef64bc49668727834bf9e30` -> `CHECKPOINTED`.

Installed-session evidence:

- stale NSIS self-delete residue was proven to be an empty target with no process before conditional removal: run `1151d304b5864708ad6f694d9fd91b6c`, wave `fc5cc270eec8419b93c57e78b2871d0f`;
- fresh controlled installation and exact installed Supervisor hash: run `dfc0f3be347540989489dbf10574b48f`, wave `9406a7adde4b4fadb459237cd6fba1ce`;
- real Scheduled Task principal/action/triggers/manifest identity: run `44add57e789e4b14bcef1588f0e371b9`, wave `730ddc9e526b4c4981ca1c82e257196c`; raw Task Scheduler `UserId=Admin` and Windows identity `DESKTOP-63643J4\Admin` resolved to the same canonical SID;
- continuous Supervisor reached `healthy` on the existing Recovery Host without replacement;
- installed `Action Once` observed the exact existing Recovery Host and returned `last_spawned_pid=null`; scheduled-loop resume again reached `healthy`: run `f8219ca3acf8470ca39a86bedf546dad`, wave `6682903e59f549b3b721275a99788fe8`;
- authenticated product-native Recovery Host IPC plus independent Recovery/listener checks proved primary `mcpRunning/nativeAlive/tunnelRunning/fullyReady=true`, Recovery Host/MCP/Tunnel healthy, exact device lifecycle identity, and one expected listener each on ports `18766`, `18767`, `18082`, and `18083`: run `0d3dc1349077416680946c08c76875ef`, wave `68c8cab1593f46249c3f801d7e85cdcf` -> `CHECKPOINTED`;
- acceptance baseline Recovery Host remained PID `32536`, instance `399ea2ec2d751b606a2ffe7788727ac6` throughout the installed-session proof;
- mandatory Supervisor rollback removed the Scheduled Task and `%LOCALAPPDATA%\WebMcpRecoverySupervisor`, persisted status returned to `uninstalled`, the controlled acceptance app was preserved for isolated packaged fault testing, and primary/recovery runtime health remained intact;
- final rollback verification: run `f64f9aac35d8459e903524953b3e0943`, wave `855626394161448fa5ea98ed60c61c62`, accepted P0.2 proof fingerprint `886ab2d4e0bbee7c89d62fb7124a979aae241f6cd849983193efa77899697d2f` -> `CHECKPOINTED`.

Harness/control observations explicitly excluded from product-regression classification:

- Task Scheduler normalizes the same-user principal string (`Admin` vs `DESKTOP-63643J4\Admin`); canonical SID equality proved identity;
- anonymous `GET /__control/health` correctly returned `401 Unauthorized`; final proof used shipped authenticated Recovery Host IPC;
- a temporary Electron `safeStorage` helper produced no result and was abandoned/cleaned rather than used as evidence;
- one post-rollback PowerShell check used the reserved automatic `$PID` variable and failed with `VariableNotWritable`; the corrected `$ownerPid` read-only check passed without repeating rollback.

Current external state after P0.2 rollback:

- `WebMCP Recovery Supervisor` Scheduled Task: absent;
- `%LOCALAPPDATA%\WebMcpRecoverySupervisor`: absent;
- persisted Supervisor state: `uninstalled`;
- `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4`: preserved for P0.3 isolated packaged fault testing;
- development Recovery Host, primary/recovery MCP, and both Tunnels: healthy/coherent at final proof.

**Persistence boundary:** true reboot/logon resurrection has not been executed from a control topology that can survive and independently verify the reboot/logon result. It remains an explicit external acceptance item and is not inferred from the current-session proof.

## 7. P0.3 — Recovery fault matrix

Run only after P0.2 fixed-package current-session acceptance is green. Destructive faults that could sever the current Coding MCP control plane must run in an isolated packaged real-process harness rather than against the active control connection. Do not label an isolated proof as a live-production kill.

Every case requires exact target PID/process fingerprint, bounded timeout, post-condition identity checks, and rollback/cleanup.

| Case | Fault | Expected recovery | Critical assertions |
|---|---|---|---|
| F1 | UI/Electron process exit/restart | Recovery Host + primary/recovery planes survive; UI reconnect is independent | no duplicate authority; primary/recovery listeners remain coherent |
| F2 | Recovery Host owned PID exit | installed Supervisor restores exact fixed `--recovery-host` | new host PID/instance; no foreign adoption; existing healthy subordinate ownership preserved/proof-gated |
| F3 | Recovery MCP owned PID exit | Recovery Host restores Recovery MCP | new Recovery MCP PID; expected port/device identity; no duplicate listener |
| F4 | Recovery Tunnel owned PID exit | Recovery Host restores Recovery Tunnel | new Tunnel PID; Recovery MCP preserved; health endpoint returns |
| F5 | primary MCP owned PID exit | Recovery Host restores primary MCP per policy | same workspace/device identity; healthy primary Tunnel preserved unless policy explicitly requires otherwise |
| F6 | primary Tunnel owned PID exit | restore only primary Tunnel | primary MCP PID preserved; new Tunnel PID; healthy port |
| F7 | stale lock/ownership fixture | stale lock safely reclaimed only with proof | no foreign kill/adoption; single owner after recovery |
| F8 | live-but-unhealthy/hung owner fixture | fail closed before any replacement | no premature kill; no duplicate process/listener; typed blocked-live-owner evidence |
| F9 | repeated Recovery Host crash | bounded backoff/suppression | no crash loop; restart limit/window/suppression respected |

Additional immutable guard cases already covered by packaged/focused tests remain required in the RC suite:

- executable/manifest hash mismatch -> fail closed, no arbitrary spawn;
- handoff failure -> one owner/lock, terminal activation state, no orphan/duplicate listener.

True reboot/logon persistence is tracked separately as the P0.2/P1 external persistence acceptance boundary when it cannot be safely verified in-session.

Post-case invariant: no active orphan/overlap/stale EOCL run, no duplicate listeners on primary/recovery MCP and health ports, and all owned state identities are coherent.

## 8. P1.1 — Exact-fingerprint release candidate

Run once after P0 source changes stop:

- `git diff --check`
- `npm test`
- full Coding MCP pytest with terminal summary preserved
- `npm run test:recovery:e2e`
- `npm run test:recovery:packaged`
- `npm run canary:opencode-flash:preflight`
- `npm audit --omit=dev`
- final `npm run dist` after all source is frozen
- installer/resource/provenance verification
- controlled live activation/instance verification for any runtime-affecting source delta
- orchestration audit: no active/overlap/orphan/stale/fence residue.

Record exact HEAD, worktree/source fingerprint, package version, installer SHA-256, test counts, skipped tests, and any accepted external blocker.

`npm run test:recovery:packaged` may regenerate/clean `dist/`; therefore the final NSIS artifact used for release-candidate identity must be built after the source/test surface is frozen.

Do not create a release/tag/publish artifact unless explicitly authorized separately.

## 9. P1.2 — Representative routing economics

### Principle

Do not create synthetic work just to reach a sample count. Enroll real accepted engineering tasks when they naturally occur. A pair is eligible only when source/task semantics/oracle/environment are comparable and provenance is `representative`.

### Initial task classes

- localized strong-oracle bugfix;
- cross-file bounded change;
- deep integration/debugging;
- test-failure repair;
- read-only research/diagnosis.

### Per-pair fields

- `pair_id`, `task_class`, `oracle_id`, `environment_id`, `cache_stratum`, `replicate_id`;
- route/policy/topology;
- accepted/rejected result;
- TTA/wall time;
- measured or provider-reported tokens/cost when available;
- critical/noncritical defects, manual repair, rollback, regression escape;
- host-observed latency only when explicit trace/turn binding exists.

### Promotion rule

A task class remains deterministic unless the runtime's representative promotion gate is satisfied. Benchmark/synthetic evidence may guide experiments but never authorize production promotion.

If the current ledger does not contain sufficient comparable representative pairs or controller cost is unobserved, record `KEEP_DETERMINISTIC / NO_PROMOTION` as the accepted gate result instead of manufacturing evidence.

## 10. P1.3 — Selective routing promotion

- Query runtime promotion readiness by task class.
- Promote only explicitly supported task classes with sufficient accepted representative pairs and quality/cost/time advantage.
- Keep other classes deterministic.
- Never auto-promote `sol_max`/`sol_ultra`.
- Auto-handoff remains independently gated even if a routing class is promoted.

If no class qualifies, record `KEEP_DETERMINISTIC` as the accepted result; that is a successful evidence-based decision, not an incomplete implementation.

## 11. P2.1 — Semantic localization optimization

Current runtime status: `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

Current binding report indicates missing origin and credential-file configuration. Do not invent credentials or expose secrets.

The accepted S3/W4 graph layer does not change this boundary: it is intentionally useful with bounded text fallback and must not be treated as evidence that the native semantic provider is configured or live.

Evaluate before implementing:

1. identify the exact provider/binding configuration required by the current runtime;
2. if the required external configuration exists, run a bounded benchmark comparing semantic-first localization vs bounded text fallback on representative repository queries;
3. measure latency, tool hops, result quality/recall, memory/process pressure, and operational fragility;
4. enable/configure only if benefit is material and does not reopen the closed P2/P3 memory/resource risk;
5. if binding configuration is absent externally, record the exact `BLOCKED_CONFIG` boundary;
6. if configured but benefit is not material, record `KEEP_TEXT_FALLBACK` and leave the correctness path unchanged.

## 12. Progress log

### 2026-08-21 — S5 / W6 Single-Checkout Mutation Coordinator accepted

- Exact W6 lease/admission contract was recovered before mutation. Existing EOCL + durable SQLite workspace write-fence authority was augmented rather than replaced; no worktree/promotion/second-coordinator subsystem was added.
- Lease/recovery now bind source-writer session, source/runtime fingerprints, allowed/protected paths, preexisting dirty source paths, start time, and lease state. Pre-write admission fails closed on session/base/source drift, foreign dirty paths, scope/protected-path violations, expired/foreign fences, and candidate paths outside bounded scope.
- Candidate/reviewer lanes remain proposal/read-only and cannot directly mutate the canonical checkout; MCP still owns source application after admission. `.coding-tools` evidence churn remains outside source identity contention and smart-v3 remains exactly 8 public tools.
- Initial run/wave `f2bda257239346f089ccf073f38d4790` / `485fabde2223430bb42408adcc48b406` was **not accepted** after proof `2b4df408c0ea4b539a6098fccfa15c99` reported 1 failed / 23 passed. EOCL revoked the write lease and required REPLAN.
- Fresh-wave diagnosis proved the lone broad-suite failure was a stale hard-coded expected tool-contract SHA (`bd5c...` expected vs current runtime `e942...`), unrelated to S5 public-surface behavior. The assertion was deliberately left unchanged rather than edited for false-green status.
- Final acceptance review added two genuine hardening details—case-folded protected roots and Execution-Hub-record-bound `owner_session`—and a regression for uppercase `.GIT` bypass.
- Fresh replan wave `779af9e5182a4fafbec31ac4dfee7521` passed focused acceptance **19/19** with proof `657e21d54803457688e85f8d506f2a98`, proof fingerprint `65cfcaf39b87e63221ad873f4e0c1b1c676e531c13f31d42af7f0c7bf47fb2fc`, and runtime source fingerprint `7b35c0050e8a9ea0d96748104dea6336376f18c00c88f799f37d9fb01f29ea48` bound into the proof summary.
- Final source delta: 6 files, 379 insertions, 10 deletions; `git diff --check` clean. EOCL audit found no violation, released the write lease, recorded the accepted artifact, and explicit ChatWeb acceptance terminalized the run/wave as `COMPLETED`.
- No commit, push, tag, release, or publish was performed. S6 remains blocked until its exact maintained contract is recovered.

### 2026-08-21 — S4 / W5 Context Compiler accepted; efficacy gate keeps it shadow-only

- Exact W5 compiler/evaluation contract was recovered before mutation; no S5/W6 behavior was inferred or started.
- Implemented deterministic internal `compile_context(...)` with budget, dedupe, scope, already-seen suppression, stale omission, rules/config/diff selection, uncertainty, omitted-reason accounting, and stable fingerprints.
- Treatment is deliberately `off|shadow` only; invalid/`inject`/`auto` values fail closed and model-facing selected context remains unchanged in shadow mode.
- ChatWeb Sol rejected one green source wave because the input fingerprint did not bind evidence omitted from the compiled output. The accepted replan hashes the complete supplied `current_evidence` into `input_sha256`, with a regression proving omitted-evidence changes remain audit-visible.
- Source acceptance: run `9d1698e4267e4d118144fac810dbe4aa`, wave `1bb808f20b5741be8fd5cd91b0a76a85`, proofs `a4b9c83e3adb473e9f8eb34c452f60bf`, `888c6774db834719a0d9dc7c07e7c2ab`, `d26113ebdc7a49aca861a9bc94ef83ae` -> `CHECKPOINTED`.
- Real-ledger paired evaluation used baseline `chatweb_mcp` vs treatment `context_compiler_shadow`, thresholds 10 representative pairs / 4 task classes, and did not create synthetic/replay work. Across 794 ledger runs there were zero pair-tagged comparable treatment runs, so pair count and task-class count were both zero; cost was also incomplete because controller cost is unobserved.
- Evaluation acceptance: run `b204662b3c8748bba2bfbe3f02de1ea6`, wave `2165d6ccafb94ef4b5ce05ee6984b18d`, proofs `afbba58874f54b138040b087edc841ff`, `545d02d13ba74b10807032585e8fa363`, `acdd074415bb4b3395f298c583bd574d` -> `CHECKPOINTED`.
- Final S4/W5 decision: **KEEP_SHADOW / NO_PROMOTION**. Auto-injection remains unavailable until future representative comparable evidence clears the efficacy gate.

### 2026-08-21 — S3 / W4 Semantic Repository Graph MVP accepted

- Exact S3/W4 scope was recovered before mutation; no later-phase semantics were inferred from the S2 gate alone.
- Implemented one internal read-only bounded `SemanticRepositoryGraph` derived from existing semantic/text localization results; no public ninth tool, endpoint, DB, provider authority, credential path, or origin bypass was introduced.
- The graph supports bounded symbol resolution, references, related tests, and impact lookup; records are source-hash bound and carry provider/version/confidence/completeness plus explicit current/stale semantics.
- Large-file identity remains bounded/partial, text fallback remains lower-confidence/partial, and model-facing integration exposes only content-free status.
- ChatWeb Sol rejected two green-but-incomplete waves before final acceptance: first for false stale due mismatched refresh sample budget, then for lifetime record accumulation. Both received discriminating regressions and were fixed without widening scope.
- Final acceptance: run `c074433369cd42e1b60fb66c21454980`, wave `f02b50c4268b4ee19a0d0dfe794800bd`, proofs `cd100e39667444a89a5a77cc8bcc1661`, `438ecaec03df482c9e666eb434bdd9ca`, `eb7f022e05524075a6d998ace55a2db2`, integrity `checked=93` -> `CHECKPOINTED`.
- Native semantic provider remains `NATIVE_LSP_BINDING_NOT_CONFIGURED`; this phase is accepted in provider-degraded/text-fallback mode and does not claim native provider activation.
- S4/W5 and later phases remained gated until their exact maintained contract was recovered.

### 2026-08-21 — W1/W2A/S2 sparse/artifact closeout checkpoint

- W1 remains **ACCEPTED / CHECKPOINTED** with focused proof `19b125e7316942c0b200d52063b031af`.
- W2A is now explicitly **ACCEPTED / CHECKPOINTED** at run `214411ecb15d4d3a9f24f2be976d40a0`, wave `cff215da46404f6e82803c6a41b0a25d`; the accepted matrix covers compile/format plus over-limit rejection, bounded streaming, and target fallback.
- S2 found one real provenance gap in EOCL-owned retained command output: `owner_run`/`owner_wave` were dropped after command admission. The minimal patch in `artifact_refs.py` + `task_state.py` with focused regression coverage was accepted at run `2166c986b3b54cab8804ec8fff87a93b`, wave `165330542f8d4d8f94bc09676600c112`.
- Final S2 proof-only closeout passed 6/6 focused proofs and was **ACCEPTED / CHECKPOINTED** at run `3b978ca3ccb840c1aee84bc122b2a4a6`, wave `765f375570f842f28ae5403d1f643378`; no file changes occurred in that final wave.
- S2 acceptance covers real producer/ledger/build refs, bounded project-artifact reads, complete bounded image reads, MIME spoof rejection, and source-inspected SHA-256 verification before MCP native-image framing.
- Broad root-suite failures previously seen in Windows temp cleanup/source-bundle state were outside the S2 acceptance surface and were not used as S2 oracles.
- S3 was never mutated before S2 acceptance. It opened only after the accepted S2 checkpoint, and its exact semantic-health/W4 graph scope was recovered from maintained project evidence before implementation.

### 2026-08-17 — Plan initialized

- Baseline HEAD: `3059b218989fda8ebf217d121cd6e8f74a71587d`.
- Maintained docs confirmed packaged Recovery existed but installed persistence proof remained a release boundary.
- `execution_route=auto` intentionally remained deterministic pending representative paired evidence.
- Native semantic localization reported `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

### 2026-08-17 — P0.1 complete and delivered

- Runtime-only host-correlation + SQLite sidecar Git hygiene closed.
- Canonical `ledger.sqlite3` tracking proven intact.
- Source-root cleanliness PASS.
- EOCL final acceptance `CHECKPOINTED`.
- Delivered: `bae11481 chore: close runtime evidence hygiene`.

### 2026-08-17 — Full `.coding-tools` retention supersedes P0.1 exclusions

- Project retention policy changed from selective runtime-only exclusions to full `.coding-tools/**` versioning for historical analysis.
- Repository-local `.coding-tools` ignore rules are removed and an explicit keep-visible rule is authoritative.
- `check:coding-tools-history` guards against ignored evidence/nested gitlinks; `check:coding-tools-delivery` additionally requires every current `.coding-tools` mutation to be staged before delivery.
- Dated research snapshots remain chronological evidence only and do not override this maintained policy or `AGENTS.md`.

### 2026-08-18 — Transient SQLite sidecars explicitly excluded

- Operator direction now permanently excludes only `.coding-tools/orchestration/ledger.sqlite3-shm` and `.coding-tools/orchestration/ledger.sqlite3-wal` from Git delivery because they are transient SQLite sidecars and have caused commit instability.
- Canonical `.coding-tools/orchestration/ledger.sqlite3` remains mandatory repository evidence, together with every other `.coding-tools` artifact.
- Repository policy/guard must enforce that the two named sidecars are ignored and untracked without permitting any broader `.coding-tools` exclusion.

### 2026-08-17 — P0.2 first installed attempt found packaging blocker

- Exact NSIS installer from `bae11481` built and installed to a controlled per-user target.
- Real Scheduled Task registration succeeded structurally but runtime `Action Once` failed.
- Root cause proven: packaged Recovery Supervisor bytes were stale versus source, so the Unicode-path handling fix was absent from installer.
- Scheduled Task rollback PASS; no persistent project/runtime evidence deleted.

### 2026-08-17 — Packaging exact-source remediation delivered

- Clean-dist prepackage boundary added.
- Full allowed `resources/` byte-identity afterPack gate added.
- Packaged Recovery smoke gained source hash guard.
- 13/13 focused tests PASS.
- Full exact-source identity PASS for 249 files.
- Full packaged Recovery smoke PASS after terminal Electron Builder run.
- Delivered: `d5d4bbb5 fix: enforce exact-source packaged resources`.

### 2026-08-17 — Fresh `d5d4bbb5` NSIS build accepted

- EOCL run `3ca4f890a8ae4090ac9858c0b0e68d46`, wave `16b3281053d24c32941153b9ab1fc428` -> `CHECKPOINTED`.
- `npm run dist` exit `0`.
- Installer size `128670087` bytes.
- Installer SHA-256 `A81AAB1C1399F4E8D57E090CBA25E5B6A939EDE2F9EB60E9C2C8A8E10C723AE2`.
- Packaged supervisor exactly matched source hash `540730E4...`.

### 2026-08-17 — P0.2 second installed attempt found persisted-state blocker

- Fresh exact-source package installed successfully to `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4`.
- Installed supervisor hash matched package/source exactly.
- Real Scheduled Task structure/principal/triggers/manifest were correct.
- Task runtime returned `LastTaskResult=1`.
- Direct installed `Action Once` proved exact failure: missing `last_healthy_at` on sparse persisted `uninstalled` status under StrictMode.
- Scheduled Task rollback PASS; supervisor install root removed; persisted state returned to `uninstalled`.

### 2026-08-17 — Sparse persisted-state remediation source accepted

- `New-State` now normalizes only missing optional persisted fields to safe defaults.
- Existing fail-closed casts, ownership checks, thresholds, manifest identity, mutex and restart policy remain unchanged.
- Exact sparse-uninstalled regression added.
- Focused Recovery Supervisor test: **12/12 PASS**.
- Scoped diff hygiene: PASS.
- Remediated source SHA-256: `E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420`.
- EOCL run `274bd626bfb44943afedb3e755002ad0`, wave `62183559c12943ec8e9a9dec25c4f257` -> `CHECKPOINTED`.
- Delivered as `acaa3582 fix: normalize recovery supervisor persisted state`; `origin/main` aligned before the final P0.2 installer build.

### 2026-08-17 — P0.2 current-session installed acceptance complete

- Fresh exact-HEAD installer from `acaa3582`: `128670108` bytes, SHA-256 `0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879`.
- Packaged Supervisor exactly matched source SHA-256 `E0B906C1...`; exact packaged resource projection passed for 249 files.
- Real same-user Limited Scheduled Task reached continuous `healthy` on the existing Recovery Host.
- Installed `Action Once` observed PID `32536` / instance `399ea2ec2d751b606a2ffe7788727ac6` with no replacement; scheduled-loop resume returned healthy again.
- Product-native authenticated Recovery Host IPC + independent listener/Recovery checks proved primary/recovery planes coherent and fully ready.
- Mandatory Supervisor rollback PASS: task/root absent, status `uninstalled`, controlled acceptance app preserved, runtime remained healthy.
- Final accepted rollback proof: run `f64f9aac35d8459e903524953b3e0943`, wave `855626394161448fa5ea98ed60c61c62`, proof fingerprint `886ab2d4e0bbee7c89d62fb7124a979aae241f6cd849983193efa77899697d2f` -> `CHECKPOINTED`.
- True reboot/logon persistence remains an external/unverified acceptance boundary; no persistence PASS is inferred.

## 13. Next action

1. recover the exact maintained **S6 / next closure-phase** definition and acceptance contract from the canonical technical plan before any S6 source mutation; S5/W6 is accepted/terminal `COMPLETED` and must not be broadened implicitly into a new authority or trust boundary;
2. preserve the accepted S5 one-writer design: reuse the existing EOCL/SQLite workspace write-fence authority, keep candidate/reviewer lanes no-write, and treat source/session/foreign-dirty/scope/protected-path drift as fail-closed REPLAN conditions;
3. preserve Context Compiler as internal/default-off/shadow-only until future real representative paired evidence independently clears its efficacy gate; do not manufacture treatment pairs and do not add auto-injection merely because the source exists;
4. selectively deliver the accepted closure evidence boundary while preserving unrelated concurrent source work, and include the **complete current `.coding-tools/**` deliverable tree** in any project-state commit/push; exclude only `ledger.sqlite3-shm` and `ledger.sqlite3-wal`, while retaining `ledger.sqlite3`, host-turn state, and runtime projections;
5. execute P0.3 F1-F9 where independent of the next closure phase, reusing exact existing deterministic/E2E coverage where sufficient and using an isolated packaged real-process harness for destructive cases that could sever the active Coding MCP control plane;
6. update this file with per-case fault evidence, post-case ownership/listener/orphan invariants, and any minimal remediation required by a reproducible fault;
7. freeze source and execute the exact-fingerprint RC gate, rebuilding the final NSIS artifact only after the source/test surface is frozen;
8. evaluate representative routing evidence; if comparable accepted cohorts are insufficient or cost remains unknown, record `KEEP_DETERMINISTIC / NO_PROMOTION` rather than manufacture evidence;
9. close native semantic localization as `BLOCKED_CONFIG` unless the required external origin + credential-file binding exists, and benchmark it only if that binding is actually available;
10. record the true reboot/logon persistence boundary as external/unverified unless it is independently executed and observed;
11. make the final selective delivery commit/push including the complete `.coding-tools/**` history/evidence tree except the two named transient SQLite sidecars; do not create a release/tag/publish artifact without separate authorization.

## 14. 2026-08-21 S6-S9 closure addendum — authoritative current closure state

> **Authority note:** this addendum records the later S6-S9 work completed after Sections 3, 4, 12 and 13 were written. For the S6-S9 closure-phase status and the immediate next action, this section **supersedes older statements above that say S6 is not started, blocked pending contract recovery, or is the next phase**. Earlier sections remain intact as chronological evidence. This addendum does not supersede the independent P0.3/P1 release-candidate/persistence gates.

### 14.1 Final S1-S9 closure matrix

| Stage | Workstream | Final decision | Evidence / boundary |
|---|---|---|---|
| W1 | Sparse model-facing results | **ACCEPTED / CHECKPOINTED** | focused proof `19b125e7316942c0b200d52063b031af` |
| W2A | Bounded artifact import/streaming | **ACCEPTED / CHECKPOINTED** | run `214411ecb15d4d3a9f24f2be976d40a0`, wave `cff215da46404f6e82803c6a41b0a25d` |
| S2 | Artifact/resource closeout | **ACCEPTED / CHECKPOINTED** | final run `3b978ca3ccb840c1aee84bc122b2a4a6`, wave `765f375570f842f28ae5403d1f643378` |
| S3 / W4 | Semantic health + repository graph | **ACCEPTED / CHECKPOINTED — PROVIDER-DEGRADED** | run `c074433369cd42e1b60fb66c21454980`, wave `f02b50c4268b4ee19a0d0dfe794800bd`; native provider remains unconfigured |
| S4 / W5 | Context Compiler + efficacy gate | **ACCEPTED / CHECKPOINTED — KEEP_SHADOW / NO_PROMOTION** | source run `9d1698e4267e4d118144fac810dbe4aa`; efficacy run `b204662b3c8748bba2bfbe3f02de1ea6`; zero comparable representative pairs |
| S5 / W6 | Single-checkout mutation coordination | **ACCEPTED / CHECKPOINTED — COMPLETED** | run `f2bda257239346f089ccf073f38d4790`, final wave `779af9e5182a4fafbec31ac4dfee7521`, 19/19 focused PASS |
| S6 / W7 | Capability policy + Secret Broker + isolated-worker gate | **ACCEPTED / CHECKPOINTED — PRIVILEGED WORKER FAIL-CLOSED** | run `5e7915c474714154b7ac0f89a43f741d`, wave `1f74ab333f94410da7d263ddc101516b`, 6/6 focused proofs PASS; no verified full-isolation backend exists, so worker remains blocked |
| S7 / W9/W10/W11/W13 | Content-address foundations + Trace Context + MCP-2026/task isolation + process lifecycle | **ACCEPTED / CHECKPOINTED** | run `57807dae8bf94b578d78ab96d7f3b135`, final wave `21a29a1b540d4d99a43676293ee6cf3f`; broad `npm run test` PASS |
| S8 / W8 | Computer Use | **DEFERRED / GATE-CLOSED — ACCEPTED DECISION** | no first-class bounded Computer Use executor or concrete product consumer; no false privileged plane was created |
| S8 / W12 | Reverse relay/device lease | **DEFERRED / GATE-CLOSED — ACCEPTED DECISION** | current device/tunnel ownership is fail-closed, but no project grant + expiring lease + reconnect epoch/token + explicit revocation contract exists; current scope remains current-device/local-registry |
| S9 / W14 | Solution-shadow evaluation | **ACCEPTED / CHECKPOINTED — SHADOW-ONLY / NO PROMOTION** | final proof run `4fb70ab0823148af83ff006f6203cb57`, wave `528e57a47d6a4f348eb62b678a4ea474`, 21/21 solution-economics tests PASS |
| S9 / W15 | External A2A interoperability | **DEFERRED / GATE-CLOSED — ACCEPTED DECISION** | exact source audit found no A2A/Agent Card/external A2A consumer; internal polling/websocket/QUIC runner protocols are not treated as A2A |

**Closure interpretation:** the **S1-S9 implementation/control program is closed for the approved baseline**. “Closed” means every stage has either (a) accepted implementation evidence or (b) an accepted fail-closed/deferred gate decision where prerequisites/use case are absent. It does **not** mean deferred privileged capabilities are released, nor does it mean the independent exact-fingerprint RC, P0.3 fault matrix, true reboot/logon persistence, delivery commit/push, tag, publish, or production release has been executed.

### 14.2 S6 / W7 — Capability Policy, Secret Broker, and isolated-worker gate

- Status: **ACCEPTED / CHECKPOINTED**.
- EOCL run: `5e7915c474714154b7ac0f89a43f741d`.
- EOCL wave: `1f74ab333f94410da7d263ddc101516b`.
- Focused acceptance: **6/6 PASS**.
- The accepted security work adds/uses an internal capability-policy basis, a scoped Secret Broker, and bounded child-environment construction rather than passing broad host environment/secrets into sensitive child processes.
- Secrets remain owned at rest by the existing Electron secret store; privileged launch paths resolve only the scoped secret material needed at the process boundary. Model-facing/tool-facing state does not gain raw-secret authority.
- The public MCP surface remains exactly **8 smart-v3 tools**; S6 introduced no ninth privileged tool and no second authorization authority.
- Existing process-tree/job-object lifecycle controls remain lifecycle evidence only; they are not falsely promoted to filesystem/network sandbox guarantees.
- **Critical accepted boundary:** `code_mode_worker_isolation_status()` remains **blocked/fail-closed** because no verified backend currently proves all required guarantees simultaneously: no direct filesystem, no network, no inherited environment secrets, no unrestricted subprocess, and bounded framed host-binding-only IPC. Windows Job Object and Linux Landlock partial primitives are explicitly insufficient by themselves.
- Therefore S6 acceptance means the security foundation and fail-closed worker gate are correct. It does **not** claim an isolated arbitrary Code Mode worker is live.

### 14.3 S7 / W9, W10, W11, W13 — traceability/runtime robustness closeout

- Status: **ACCEPTED / CHECKPOINTED**.
- Final run: `57807dae8bf94b578d78ab96d7f3b135`.
- Final remediation wave: `21a29a1b540d4d99a43676293ee6cf3f`.
- Proof fingerprint: `244c225f63362fc1c97761d00da29ec8ce948faa733104544dcc8f106d833cb0`.
- W10 adds W3C Trace Context validation/propagation through the existing MCP request/background/Hub Proxy path. Host-generated trace IDs are 128-bit W3C-valid. Raw `tracestate` is not persisted as ledger content.
- W11 keeps MCP-2026/stateless request behavior and task-context isolation on the existing authority boundary; no duplicate public protocol authority was added.
- W13 retains durable managed-process admission/restart/orphan reconciliation and process-tree cleanup; acceptance does not reinterpret process lifecycle as a security sandbox.
- W9 reuses existing content-address/hash foundations where already sufficient; no speculative standalone CAS service/store was introduced merely to satisfy a label.
- Focused accepted proofs:
  - `e238660db66443369d398fcc98547d7c` — Trace Context + MCP-2026, **15 pytest + 10 subtests PASS**;
  - `38a95d27175643a2a859a706c9889ea9` — Hub Proxy trace/header behavior PASS;
  - `5d6cc484cc1841f4aa38d1e8fc0cb4d3` — Execution Hub, **9 PASS**;
  - `9b792bbd174d4556873afb1db524fa40` — managed process/restart, **21 PASS**;
  - `0c1c749b00bf46468029320cd5c2d4b8` — `git diff --check` PASS.
- Broad root verification initially reported **246/247** due to pre-existing private runtime state under `resources/coding-tools-mcp/.coding-tools`, not a Trace Context assertion failure.
- Investigation proved the nested source-package state contained a stale misplaced `orchestration/ledger.sqlite3` (262,144 bytes; last written 2026-08-20) while the canonical root ledger remained the active multi-megabyte evidence store. The misplaced ledger had no associated WAL/SHM/journal/report set.
- Evidence was preserved before cleanup: the misplaced ledger was copied to `.coding-tools/orchestration/recovered/misplaced-ledger-20260820T101338Z.sqlite3`, and `fc /b` proved byte-for-byte identity before the wrong-location copy/directories were removed.
- Recovery/remediation proof IDs:
  - `2d307ce7b6ab41f2a40af2af4e987987` — recovery directory;
  - `24035aff1d91419f8ba29b60ad14f70b` — lossless copy;
  - `042f81ea54904dd6bd7040458c160d11` — byte comparison;
  - `c32961ecbcc84b6daf1ac6dedd95453a` — removal of the verified misplaced copy;
  - `a209dccdb25b4c0daa758968408aa71a` — source-bundle guard PASS;
  - `43adaeba58e84f15b8ee1c0769aeb917` — W10 focused re-proof PASS.
- After recovery, **full `npm run test` exited 0** and `git diff --check` passed. The source-bundle guard remains strict; no `.gitignore` weakening or history deletion was used.

### 14.4 S8 / W8 + W12 — accepted privileged-capability gate decision

- Status: **ACCEPTED GATE DECISION**.
- EOCL run: `399d5420e538444eb618fc72eb65487f`.
- EOCL wave: `89865d70f047498f85acc318637f32aa`.
- Proof fingerprint: `1775d099bea4e58f3f2c171f385ba286fd49b766ee96e8c934e42c4a795efa2e`.

**W8 Computer Use**

- Decision: **DEFERRED / GATE-CLOSED**.
- Current Electron window/clipboard primitives are not represented as a Computer Use executor.
- The repository does not currently provide the bounded screenshot/snapshot, click, keyboard, scroll, display/window-selection, opt-in clipboard, and sensitive-action approval policy surface required by the maintained W8 contract.
- Credential dialogs, destructive OS controls, payment/financial flows, and secret-bearing clipboard actions therefore remain outside any automated Computer Use authority.
- No concrete product consumer was found that justifies opening a new privileged control plane now. No fake/stub Computer Use feature was created.

**W12 reverse relay/device lease**

- Decision: **DEFERRED / GATE-CLOSED**.
- Existing foundations already provide device identity/instance binding, tunnel fingerprint, workspace/device health checks, foreign/unverified-owner fail-closed behavior, recovery candidate readiness/handoff, and an independent recovery tunnel.
- A first-class W12 authority still requires a project grant, expiring connection lease, reconnect token/epoch, stale-authority invalidation, explicit revocation, and duplicate-job prevention across reconnect.
- Current product scope remains `current_device_only` with a local registry. Adding a few JSON fields without the full authority contract would be false security and was explicitly rejected.
- Accepted focused proofs:
  - `24cd169399484ebd8eb648f566a479e8` — runtime/device ownership fail-closed behavior PASS;
  - `0f0c9c1e85824fd88514961e75302779` — recovery/tunnel foreign-owner, candidate-handoff and invalid-config fail-closed behavior PASS;
  - `0b757c1ad41749b08e1d966316f6af24` — diff hygiene PASS.

### 14.5 S9 / W14 + W15 — shadow evaluation accepted; A2A gated

- Status: **ACCEPTED / CHECKPOINTED** for W14 and **ACCEPTED DEFER/GATE-CLOSED DECISION** for W15.
- Final proof run: `4fb70ab0823148af83ff006f6203cb57`.
- Final wave: `528e57a47d6a4f348eb62b678a4ea474`.
- Proof fingerprint: `86b03a6d5ac4689ad8fe760cc174a23f73d7511378dbdf1c166bec5f0c41f302`.
- Final W14 proof: `7555fc12976b494c9c40eff47c17463d` — `tests/test_solution_economics.py`, **21/21 PASS**.

**W14 solution-shadow evaluation**

- Existing implementation was proven sufficient; no new source mutation was required for final S9 acceptance.
- Shadow recommendation recording is limited to eligible feature/bugfix workflows and the active wave, and is rejected after the first `write_lease_acquired` event.
- Recommendation IDs are idempotent for identical evidence and fail closed on conflicting reuse.
- Stored recommendation/evaluation fields are bounded/content-free; patch/touched-surface evidence uses counts/identities rather than source content.
- `solution_shadow_run_report` reconstructs the accepted outcome and explicitly compares recommendation-estimated surfaces against the actual touched surface while preserving source-state/proof lineage.
- Policy fields remain `automatic_policy_activation=false`, `production_behavior_changed=false`, `shadow_only=true`, and `p5_automatic_start=false`.
- Representative provenance remains required for predictive promotion evidence; benchmark/synthetic/unlabeled evidence cannot promote production behavior.
- The accepted behavior is therefore **SHADOW-ONLY / NO PROMOTION**, consistent with the S4/W5 efficacy decision.

**W15 external A2A interoperability**

- Decision: **DEFERRED / GATE-CLOSED**.
- Exact source search for A2A/Agent Card/`.well-known` A2A/media-type artifacts found no concrete external A2A consumer or first-class A2A integration.
- Existing `polling-v1`, `websocket-v1`, and `quic-v1` agent/runner protocol versions are internal runner transport/versioning and are **not** claimed as W15 external A2A interoperability.
- No speculative Agent Card, cross-runtime agent mesh, second authority, or compatibility layer was created solely to mark W15 complete.

### 14.6 Current intentional gates after S9

The following are deliberate, evidence-backed gates and must not be reinterpreted as missing unfinished coding work:

1. **Context Compiler auto-injection:** OFF. S4/W5 remains `KEEP_SHADOW / NO_PROMOTION` until real comparable representative pairs clear the efficacy gate.
2. **Automatic non-deterministic routing/policy promotion:** OFF unless representative accepted evidence satisfies the maintained promotion rules.
3. **Native semantic provider:** `NATIVE_LSP_BINDING_NOT_CONFIGURED`; S3 graph remains valid in provider-degraded/text-fallback mode.
4. **General isolated Code Mode worker:** BLOCKED/FAIL-CLOSED until one backend proves all W7 isolation guarantees; Job Object/Landlock partial guarantees are insufficient.
5. **Computer Use:** W8 DEFERRED/GATE-CLOSED until there is a concrete consumer plus bounded action surface and sensitive-action policy.
6. **First-class remote reverse-relay/device lease:** W12 DEFERRED/GATE-CLOSED until project-grant/expiry/reconnect/revocation semantics and a concrete remote-device use case exist.
7. **External A2A:** W15 DEFERRED/GATE-CLOSED until a concrete external consumer exists.
8. **True reboot/logon persistence:** still external/unverified; current-session Scheduled Task evidence must not be upgraded to reboot/logon proof.
9. **P0.3 production Recovery fault matrix:** remains a separate release-hardening workstream; destructive cases must use the isolated packaged harness where the active control plane could be severed.
10. **Exact-fingerprint RC/release:** not executed by S1-S9 closure. A new exact-HEAD final package/installer proof is required after source/docs freeze if release acceptance is requested.

### 14.7 Delivery state for this closure session

- The S6-S9 source/proof/control work above was completed without a release/tag/publish action.
- **No commit or push was performed in the S6-S9 closure session described by this addendum.** This is intentional because no separate commit/push instruction was issued during this continuation.
- Any later delivery must include the complete current `.coding-tools/**` evidence/history tree except exactly `.coding-tools/orchestration/ledger.sqlite3-shm` and `.coding-tools/orchestration/ledger.sqlite3-wal`.
- The canonical `.coding-tools/orchestration/ledger.sqlite3` remains mandatory delivery evidence. The recovered misplaced ledger under `.coding-tools/orchestration/recovered/` is also historical evidence and must not be silently dropped.
- Heavy local Excel/test artifacts remain local where they are test-only and are not part of code/history delivery.

## 15. Authoritative next action after S9 closure

The former Section 13 list is historical for the pre-S6 state. The current next-action policy is:

1. **Do not reopen S1-S9 merely for architecture polishing.** The closure program is terminal for the approved baseline, with the explicit gates in Section 14.6.
2. Continue collecting **real representative paired evidence** during normal engineering work for W5/routing economics; do not manufacture synthetic pairs for promotion.
3. Reopen a gated capability only when its named prerequisite becomes real: verified full-isolation backend (W7 worker), concrete Computer Use consumer + policy (W8), concrete remote-device lease use case + full lease authority (W12), external A2A consumer (W15), or native semantic binding configuration (P2.1).
4. If the immediate goal is **release hardening**, continue the independent P0.3 Recovery fault matrix and then freeze source for the exact-fingerprint P1.1 RC gate. Do not infer this work as already complete from S1-S9 acceptance.
5. If the immediate goal is **delivery to GitHub**, run the delivery guard and commit/push the accepted source/docs/evidence boundary, including all required `.coding-tools/**` history except the two transient SQLite sidecars. Do not create a release/tag/publish artifact unless separately authorized.
6. Keep true reboot/logon persistence explicitly external/unverified until it is independently executed and observed by a control topology capable of surviving that transition.

**Terminal closure statement:** as of 2026-08-21, **S1-S9 are closed for the current approved baseline**. The remaining items are explicit evidence/configuration/use-case/release gates, not hidden unfinished S6-S9 implementation. No release, tag, publish, commit, push, runtime restart, or deployment is claimed by this statement.
