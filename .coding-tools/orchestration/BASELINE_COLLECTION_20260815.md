# Tools-Codex-web Baseline Collection Window

**Baseline ID:** `baseline-chatweb-mcp-20260815-114314-bkk`  
**Opened:** `2026-08-15T11:43:14.778399+07:00` (`2026-08-15T04:43:14.778399+00:00`)  
**Purpose:** measure the cheapest sufficient path to an accepted result before promoting any worker route.

## Runtime/source boundary

```text
workspace: E:\DEV\Tools-Codex-web
branch: main
HEAD: dff81e251836666fc825c40bf86e4167afd29c39
worktree_fp: 6351bfb00f7926c80afb825efa115bc6befb5ce7fc9966c29b949fb2c8dfde2e
runtime_version: 0.4.3
process_instance_id: wttnOYlHgwtJXrqx
server_instance_id: cNqRmaEprI1jpa4j
smart-v3 tools: 8
contract_sha256: cf1eab62a466b2fb1c8d80f997ac61ef28255d891f13ad2f245d33015d701e86
```

The runtime was explicitly restarted by the user before this window. Live post-restart proof `run-c8bc935c8d9e4b9180c99a12e841d7fa` established:

```text
execution_route requested: auto
execution_route resolved: deterministic
reason: roi_gate_hold_insufficient_paired_evidence
provider/model selected: none
external review: disabled / skipped
source mutation: none
```

That probe is diagnostic-only and is excluded from representative baseline cohorts.

## North star

Evaluate in this order:

1. preserve quality, security, compatibility and acceptance correctness;
2. minimize **total expected cost per accepted result**;
3. minimize **time to accepted result (TTA)**, especially p50 and p90;
4. minimize rework/replan and proof duplication;
5. only then consider worker utilization or model diversity.

Agent/model call count is diagnostic, not a success metric.

## Baseline policy

Primary baseline policy is `chatweb_mcp`:

```text
ChatWeb Sol: controller, architecture, ambiguity resolution, final acceptance
Coding Tools MCP: deterministic localization/execution/proof/state
execution_route=auto: fail-closed deterministic during measurement
external semantic review: default off
Mini/Luna: explicit paired-study only
Sol xhigh/Terra: explicit-only; not part of baseline collection
OpenCode: canary/read-only only; not part of baseline collection
```

No external model should be invoked merely to increase utilization.

## Representative task classes

Initial target: **24 organic accepted tasks**, four per class when available.

| Task class | Target | Inclusion signal |
|---|---:|---|
| `localized_bug_strong_oracle` | 4 | localized defect with a strong focused reproduction/test |
| `test_failure_repair` | 4 | existing deterministic failing test/compiler/static oracle |
| `bounded_feature_single_subsystem` | 4 | settled behavior, bounded subsystem, clear acceptance oracle |
| `contract_preserving_refactor` | 4 | behavior-preserving change with focused regression proof |
| `cross_file_integration` | 4 | real cross-file implementation requiring integration judgment |
| `build_release_maintenance` | 4 | build/package/release correctness with deterministic checks |

Do not manufacture tasks to fill quotas. The window accumulates only organic work requested for the repository.

## Exclusions

Exclude from representative baseline/promotion evidence:

- benchmark fixtures, synthetic tasks, canaries, probes, smoke-only runs;
- this baseline setup/restart work;
- documentation-only research/report generation unless evaluated as a separate docs class;
- runs lacking a trustworthy acceptance oracle;
- duplicate retries that do not materially change evidence/strategy;
- external-provider experiments not requested by the paired-study protocol.

Historical pre-window runs remain forensic/reference evidence only and are not retrofitted into this baseline.

## Metrics per accepted result

Preferred normalized record:

```text
source/base/worktree identity
task_class + oracle identity
route requested/resolved
run start
first route
first external dispatch
first write
first green proof
accepted timestamp
TTA
proof duration
first-pass accepted
replan/failure count
external provider usage/cost/credits
controller pre-MCP time/tokens/cost when actually observable
total monetary cost only when complete
```

Unknown controller monetary cost is **unknown, not zero**.

## Initial snapshot

At window open, the evaluator reported:

```text
ledger_run_count: 265
tagged_runs_scanned: 0
Mini valid pairs: 0
Luna valid pairs: 0
automatic_activation: false
Mini status: HOLD / indeterminate_no_pairs
Luna status: HOLD / indeterminate_no_pairs
```

This is intentional. Historical benchmark/synthetic rows are not promoted into representative pairs.

## Client schema limitation

The live server/source schema now contains the `agent_workflow.evaluation` object (`pair_id`, `policy`, `task_class`, `oracle_id`, `provenance`, optional controller usage/cost), but the current ChatWeb connector schema cache still exposes the previous `agent_workflow` signature and therefore cannot safely send those fields in this session.

Rules while this client schema remains stale:

- do **not** edit `ledger.sqlite3` manually;
- do **not** retrofit evaluation metadata after the fact;
- do **not** use raw MCP/protocol bypass;
- ordinary post-window ChatWeb+MCP runs may be used as observational reference, but are not pair-eligible promotion evidence without explicit evaluation tags;
- begin official pair-tagged collection after a refreshed client session exposes the evaluation schema.

## Paired-study entry criteria

Once the client exposes evaluation tags, paired runs must share:

```text
pair_id
same starting source/base identity
same task semantics
same oracle_id
same task_class
provenance=representative
```

Start only with Mini/Luna subsets. Do not auto-promote. Minimum review threshold remains at least 10 valid pairs and 3 task classes before manual ROI interpretation; final savings thresholds must be learned from representative data rather than hardcoded in advance.

## Decision rule

A worker route is retained/promoted only if it preserves the quality floor and shows positive marginal value after coordination/rework costs. If ChatWeb+MCP is cheaper or faster for a task class, staying single-lane is the desired outcome.

This file is operational measurement evidence under `.coding-tools/orchestration`; it is not a release artifact and should not be treated as source-code provenance.
