# Orchestration Run Summary

- Run: `776a18b744aa4dda83ec3a7ca2986d65`
- Task: `6c26eedb641f45029f8793450f759a03`
- Objective: Produce and verify the fresh final local NSIS artifact from the accepted provenance-isolation source fingerprint. Run npm dist (including its full Node/Electron tests), then packaged Recovery smoke, git diff hygiene, source-root cleanliness, and native Windows installer SHA-256/metadata commands. This is local verification only. Do not restart the resident runtime, do not commit/push, do not deploy/publish/release/tag, and do not dispatch any provider/model.
- Status: **aborted**
- Started: `2026-08-21T04:42:06.041Z`
- Finished: `2026-08-21T04:47:35.356Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **11**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6cc62eff8184430a924d4543acbe48b2` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 2 | `6b191ad942e44d16a5c0c9f3ae3df73e` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 25994 | `deterministic` | `deterministic` | explicit_request |
| 26040 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26034 | `SOL_REJECTED` | `ACCEPTING` | Reject this final package proof wave for provenance integrity only. All six requested checks passed on source fingerprint 48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e, including npm dist, packaged Recovery smoke, diff/source-root hygiene, installer SHA-256 and metadata. However, the resident MCP runtime is still running pre-fix code and auto-bound an unrelated attendance-timesheet-crawler gh workflow command into this exact run/wave. The source fix is already accepted and full MCP 493/3 is green, but this contaminated live proof wave must not be accepted. Preserve the generated artifact; next strategy is a short independent artifact re-proof and explicit classification that resident runtime activation requires restart. |
| 26075 | `SOL_REJECTED` | `ACCEPTING` | Reject the short artifact re-proof wave because the same resident pre-fix MCP runtime again auto-bound an unrelated attendance-timesheet-crawler command (debug=true) into this exact wave. All five artifact checks passed, confirming the artifact content itself, but clean live provenance cannot be established without activating the already-accepted isolation source fix via runtime restart. Stop retrying under the stale resident runtime. Classify source engineering as closed, local artifact content as built/smoke/hash verified, and live runtime activation/re-provenance as the sole operational gate requiring explicit restart authorization. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `89`
- Chain head: `b99c477b47e14e2ec49142a681bedd518b147b56cc1d26daccf84dbe6acdfab3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
