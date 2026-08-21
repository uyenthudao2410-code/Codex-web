# CODING WEB — TRUTH RECONCILIATION CHECKPOINT

> **Observed:** 2026-08-21 (Asia/Bangkok)  
> **Workspace:** `E:\DEV\Codex-web`  
> **Purpose:** bounded current-truth checkpoint for the T0 hardening sequence. This document is an evidence/index projection, not a new source of runtime authority.

## 1. Authority rule

Current truth is resolved in this order:

1. current implementation + authoritative focused/live proof for the exact checkout/process;
2. live EOCL/runtime contract;
3. `AGENTS.md`;
4. `docs/CURRENT_STATE.md`;
5. `docs/ROADMAP.md`;
6. maintained subsystem docs;
7. research/history documents.

A source change, focused proof, EOCL acceptance, live activation, package identity and release publication are separate claims. Missing evidence remains `UNKNOWN`; it is never promoted to success by inference.

## 2. Current observed source/runtime boundary

| Claim | Observed state | Evidence / interpretation |
|---|---|---|
| Workspace | `E:\DEV\Codex-web` | canonical Coding-VP workspace projection |
| Branch | `main` | workspace/runtime projection |
| HEAD | `36ce22300aa4cb628d84d895942aeafd35b6bde6` | current Git/runtime source projection |
| Worktree | `DIRTY` | expected during accepted-but-uncommitted T1 source + durable evidence churn; this is not a release-ready claim |
| Worktree fingerprint | `de3f62477a9624a3f3d160a63c1bc072a94655e449588956b7b1dfd880c01b37` | current runtime projection at this checkpoint |
| Runtime version | `0.4.3` | connected Coding Tools MCP runtime |
| Process instance | `IQfsHIhZWVAmqb4R` | current connected process projection |
| Server instance | `GrtqA0XMJyFlY0O0` | current connected server projection |
| `smart-v3` public tools | `8` | contract count observed live |
| `smart-v3` contract SHA-256 | `abd0f63f1653afc356a31d6c2cf23b21ddd01abdaee9d014f4ffa8ad98814a14` | live contract projection |
| Native semantic/LSP | `NATIVE_LSP_BINDING_NOT_CONFIGURED` | fail-closed fallback remains current |
| Stale orchestration runs | `0` | live runtime projection |
| Orphaned background operations | `0` | live runtime projection |
| Orphaned idempotency records | `0` | live runtime projection |

The runtime/source projection reports the worktree as dirty, so this checkpoint deliberately does **not** claim that the running process contains every uncommitted T1 byte. Source acceptance and live activation remain distinct.

## 3. T0/T1 hardening matrix

| Capability / claim | Source | Focused proof | EOCL acceptance | Live activation | Package | Release |
|---|---|---|---|---|---|---|
| T0 Truth Reconciliation | `DOCUMENTED` | N/A | docs-only checkpoint | N/A | N/A | N/A |
| T1 Wave Objective Provenance | `IMPLEMENTED` in current worktree | `PASS` | `ACCEPTED / CHECKPOINTED` | `UNKNOWN` for uncommitted changed bytes; no restart requested | `UNKNOWN` | `NOT CLAIMED` |
| T2 TruthSnapshot | `NOT IMPLEMENTED` at this checkpoint | N/A | N/A | N/A | N/A | N/A |
| T3 Operator Truth Console | `NOT IMPLEMENTED` at this checkpoint | N/A | N/A | N/A | N/A | N/A |
| C1 Executable Engineering Casebook | `NOT IMPLEMENTED` at this checkpoint | N/A | N/A | N/A | N/A | N/A |

### T1 accepted evidence

- RUN: `25941039edd44267a04e3fbcd4f4f860`
- accepted replacement WAVE: `11a84503637b4eedb9aad88c51aa9e8b`
- terminal state: `CHECKPOINTED`
- checkpoint: `2248bd2c321e49b8bb63a3ce947ff620`
- focused objective-provenance regression: PASS
- full Coding Tools MCP unit regression on the accepted T1 worktree: **489 tests run, 489 PASS, 1 skipped, exit code 0** (`python -m unittest discover -v tests`, component root `resources/coding-tools-mcp`)
- final operator completion report was acknowledged before moving to the next causal task.

T1 acceptance is intentionally narrow: it accepts wave-objective provenance semantics only. It does not accept T2, T3, C1, runtime activation, packaging, or release.

## 4. P0.3 claim-plane reconciliation

| Claim plane | Status | Canonical historical evidence / boundary |
|---|---|---|
| P0.3-A Recovery core / focused engineering | `CLOSED / ACCEPTED` | RUN `ef55188d86b8409096354a56241b3971`; WAVE `0ed226510b8c469683dfe193df7de77a`; 35/35 PASS; proof `f7b08c6401b24e179e4f68881f20d9f8` |
| P0.3-B Production F1–F9 fault matrix | `PENDING / RELEASE-HARDENING` | must be proven by controlled production-like fault cases; not implied by P0.3-A |
| P0.3-C true reboot/logon persistence | `EXTERNAL / UNVERIFIED` | requires independent real reboot/logon observation; current-session evidence is insufficient |

Permanent wording rule: never collapse these three rows into `P0.3 = CLOSED`.

## 5. Maintained-document consistency check

`docs/CURRENT_STATE.md`, `docs/ROADMAP.md`, and `docs/research/260821_CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md` were inspected for the current hardening boundary.

Result:

- maintained docs already separate source/focused proof/live activation/package/release semantics;
- `CURRENT_STATE.md` and `ROADMAP.md` describe P0 live acceptance for the verified post-fix runtime without claiming that every later source byte is live;
- the master research document explicitly splits P0.3-A/B/C and prohibits reusing historical proof as proof for newer source;
- no maintained-document contradiction was found that requires rewriting the large current-state or roadmap files merely to close T0;
- T1 is recorded here as accepted while live/package/release remain unclaimed.

## 6. Next causal boundary

The next source wave is **T2 TruthSnapshot** only.

Required constraints:

- read-only internal projection over existing authoritative data;
- no new database, ledger, authority plane or public MCP tool;
- exactly four derived match states: `MATCHED`, `MISMATCHED`, `UNKNOWN`, `NOT_APPLICABLE`;
- missing evidence cannot become green;
- UI work remains outside T2 and must wait for separate T3 acceptance;
- package truth is never fabricated from Git HEAD;
- runtime activation, package and release remain separate post-source gates.

After T2: T3 Operator Truth Console -> C1 Executable Engineering Casebook -> broad affected regression -> STOP/EVALUATE.
