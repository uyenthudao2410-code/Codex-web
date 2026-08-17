# AGENTS.md — Tools-Codex-web / WebCodex Repository Guide

These are the always-on rules for ordinary repository work. Read only the linked sections needed for the current task. A deeper `AGENTS.md` governs its directory.

## 0. Current product truth and document precedence

- The current operated product is the Windows **Electron Execution Hub + Coding Tools MCP** stack. WebCodex Rust/server/runner code remains an important foundation/subsystem, but WebCodex-core docs do not automatically describe current Desktop operations.
- Resolve conflicts in this order: current implementation/focused tests/live contract -> [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) -> maintained product docs -> component-specific `docs/agent/*` / `docs/MODEL_EXECUTION.md` -> dated `docs/research/*` snapshots.
- In `smart-v3`, the public MCP surface is exactly `workspace_context`, `agent_workflow`, `task_control`, `document_workflow`, `exec_command`, `command_control`, `request_permissions`, and `view_image`. `restart_runtime` is a `task_control` action.
- `execution_route=auto` is currently evidence-gated and fail-closed to `deterministic`; do not infer automatic Mini/Luna/Terra/Sol routing from route availability or old research plans.
- Source presence, focused proof, live controlled activation, and packaged/released state are different claims. State the strongest one actually proven.
- Dated research documents are immutable chronology/evidence by default. Correct current guidance instead of rewriting old measurements to look current.

## 1. Verify and preserve

- Work only in the repository, worktree, and external target authorized by the user.
- At task start, verify the root, branch, HEAD, status, relevant changes, and recent history. Recheck only after a Git operation, an observed concurrent change, or before committing.
- Treat prompt hashes, paths, branches, and runtime state as expectations to verify, never as reasons to overwrite the actual repository.
- Preserve unrelated work. Do not reset, rebase, restore, clean, or rewrite history unless the user explicitly requests that operation.
- Inspect only the implementation, tests, documentation, and diff relevant to the task; do not bulk-read unrelated material.

### `.coding-tools` retention invariant

- Treat **every file under `.coding-tools/**`** as repository history/evidence that must remain version-controlled and be included when project state is committed/pushed. This includes `orchestration/ledger.sqlite3`, SQLite `-wal`/`-shm` sidecars, host-turn correlation state, task/performance projections, run/wave reports, logs, backups, and future telemetry artifacts.
- Never add a `.coding-tools` path to `.gitignore`, `.git/info/exclude`, a global ignore rule, selective-staging exclusion, cleanup rule, or "runtime-only" delivery exception. Automation worktrees/nested repositories must live outside `.coding-tools`; a gitlink is not a substitute for preserving the files.
- Before **every commit or push**, stage the complete current evidence tree with `git add -A -- .coding-tools`, then run `npm run check:coding-tools-delivery`. If the guard reports a new runtime mutation, restage `.coding-tools` and rerun the guard before delivery.
- `npm run check:coding-tools-history` is the repository policy guard: it must pass with no ignored `.coding-tools` files and no nested Git repository/gitlink under that tree.
- If credential/secret material is ever detected under `.coding-tools`, do **not** silently omit the file. Stop delivery, report the conflict, and remediate/rotate/move the secret so the evidence policy can be satisfied without publishing credentials. Only an explicit user instruction naming the exception may override this retention invariant.

## 2. Build the simplest useful product

- Optimize for a workflow that is simple, obvious, and easy to operate.
- Prefer the smallest direct solution. Add abstractions, configuration, modes, compatibility layers, or extension points only for a concrete current need or a demonstrated reliability problem.
- Do not build a general framework for one use case. Wait for a second concrete use case before extracting shared machinery.
- Do not design for hypothetical consumers, tenants, deployment scales, or trust boundaries that the product does not have.
- Protect real boundaries—credentials, public entry points, destructive actions, wrong-target execution, repository history, and published artifacts—without adding policy machinery for imaginary ones.
- When two designs satisfy the current need, choose the one with fewer concepts, states, configuration paths, and maintenance costs.
- For model-facing execution, prefer structured process/argv and durable Job/observation primitives over shell-text orchestration. Keep shell as an escape hatch; structured lifecycle state is the source of truth for retry safety.
- Treat demonstrated host features such as MCP App orchestration as optional adapters. Core execution and Job semantics must remain protocol-, UI-, transport-, and OS-neutral.

Product direction: [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md), [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). [`docs/MODEL_EXECUTION.md`](docs/MODEL_EXECUTION.md) is the WebCodex core execution-subsystem contract.

## 3. Follow intent and make focused changes

- The requested outcome, scope, prohibited actions, and acceptance conditions are hard constraints. Suggested files, symbols, commands, and step order are guidance unless explicitly mandatory.
- If guidance conflicts with current code or repository conventions, make the smallest adjustment that still satisfies the task.
- Do not knowingly create a bug, inconsistent state, resource leak, compatibility hazard, or false validation result.
- Prefer the smallest coherent change. Follow existing architecture and naming; avoid speculative compatibility, duplicate representations, unrelated cleanup, and broad refactors without a named current need.
- Keep only the interfaces actually affected by the change consistent. Do not touch or revalidate unrelated projections merely because they exist.
- Add focused tests for changed behavior when practical. Update documentation when public behavior or operations change.
- Ask only when required information cannot be discovered, instructions materially conflict, or proceeding could destroy work. Otherwise continue and report any material deviation.

## 4. Validate only changed behavior

Validation is evidence, not ceremony.

- Start with the smallest check that can detect a regression. Stop when sufficient relevant evidence has passed.
- Reuse a successful result from the exact same HEAD when relevant files have not changed.
- Do not rerun the same command unless relevant code changed, a rebase or conflict invalidated it, the earlier run was incomplete or flaky, or the user requested a repeat.
- Documentation-only changes do not require Cargo compilation or tests.
- Rust changes normally require affected formatting, the smallest relevant package check when compilation may be affected, and focused tests.
- Full library or workspace tests, `--all-targets`, ignored tests, real-process harnesses, and E2E scripts are not defaults. Run them only for an explicit user request, release or deployment, a genuinely cross-cutting boundary, broad conflict resolution, or when focused validation cannot cover the change. State the reason first.
- Distinguish current failures from pre-existing failures, expected negative cases, and failures resolved by a successful retry.
- Before finishing, review the diff and confirm whitespace, worktree, conflict, and active-job state.

Testing guidance: [`docs/TESTING.md`](docs/TESTING.md).

### Runtime evidence for research and evaluation

When producing repository-local research, benchmarking, postmortems, scientific evaluation, or routing/cost analysis, treat the following `.coding-tools` artifacts as first-class evidence sources when they exist and are relevant:

1. `.coding-tools/orchestration/ledger.sqlite3` — **canonical causal audit source** for runs, waves, state transitions, delegation/authority, proof lineage, replans, acceptance, and timing relationships.
2. `.coding-tools/performance.json` — dynamic performance/usage projection for tool calls, errors, cache/dedup, routing counts, bytes, and timing aggregates; snapshot it with an observation timestamp and do not present internal credit estimates as provider billing.
3. `.coding-tools/task-history.json` — archived task-level continuity/outcome records; useful for longitudinal task-class and acceptance analysis, but not a replacement for the orchestration ledger.
4. `.coding-tools/task-state.json` — current task/run/wave projection for operator/UI state; useful for present-state evidence, not full forensic history.

These files are **volatile runtime evidence and repository history, not source-code inputs**. Volatility is not permission to ignore or omit them from project-state commits. For research claims, record the observed Git HEAD, capture time/evidence window, sample size where relevant, and distinguish measured/provider-reported facts from derived estimates and scenario assumptions. If projections disagree on causal history, prefer the orchestration ledger and explain the discrepancy. Do not manually edit runtime evidence to make a report look cleaner, and do not let `.coding-tools` volatility participate in source/worktree fingerprints or invalidate otherwise matching code proof.

## 5. Protect work and keep delivery explicit

- Never print, commit, or expose credentials, authorization headers, private keys, tokens, secret files, or sensitive command output.
- Do not silently overwrite concurrent changes. Prefer guarded or conflict-detecting edits.
- Do not weaken meaningful authentication, authorization, validation, schemas, sandboxing, or tests merely to obtain a green result.
- Do not force-push, move published tags, overwrite releases, destructively reset other work, or rewrite published history without an explicit request naming the operation and target.
- Push, publish, tag, release, deploy, restart services, or alter external systems only when the task explicitly includes it and identifies the destination.
- Review status and diff before committing. Do not mix unrelated work or amend an unrelated commit.

Current Desktop release guidance: [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md). Use [`docs/agent/release-process.md`](docs/agent/release-process.md) only when releasing the WebCodex core/server/npm component it describes.

## 6. Load domain rules only when relevant

- Public runtime and API surfaces: [`docs/agent/openapi-guidelines.md`](docs/agent/openapi-guidelines.md).
- Workflow Sessions: [`docs/agent/session-model.md`](docs/agent/session-model.md).
- Authority boundaries: [`docs/agent/permission-model.md`](docs/agent/permission-model.md).
- Architecture decisions: [`docs/agent/architecture-decisions.md`](docs/agent/architecture-decisions.md).

Use these documents as sources of truth **inside their subsystem scope** instead of copying invariants into every task prompt. If they conflict with the current Desktop boundary, follow Section 0 precedence.

## 7. Report progress and completed state

- Every material work wave or batch **must end with an operator-visible status checkpoint**. Tool cards, raw tool output, and internal orchestration state are evidence; none of them is a substitute for the status report or may be the final visible state by itself.
- Emit a checkpoint when a wave completes; when a blocker causes `BLOCKED`, `REPLAN`, or `ABORTED`; before pausing or handing work to another controller; and before a task or session stops.
- Each checkpoint must state: what was completed or changed; the current Git/run/external-system state and strongest proof; any blocker or failure classification; remaining work; and the exact next action.
- During long tool sequences, report at meaningful wave boundaries instead of after every tool call. If work will continue automatically, say so explicitly before continuing.
- Never stop silently because a tool returned, failed, timed out, requested acceptance, or changed orchestration state. Reconcile or terminalize that boundary when safe, then report it. If work cannot continue, name the exact approval, evidence, or external action required.
- The final report must include the outcome, changed files or external resources, validation performed, final Git and job state, material deviations, remaining risks, and whether push, release, deployment, or service operations occurred.
