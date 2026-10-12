# MCP Web controlled rollout — final checkpoint

Observed on 2026-10-11, Asia/Saigon. Workspace: `E:/Github/Tools-Codex-web`, dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`. Primary HEAD and index are preserved; unrelated source changes remain. This checkpoint follows the owner's explicit rollout and same-scope 60-minute renewal authorization.

## Completed and strongest proof

- Ubuntu `svhome@100.116.112.22`: revision `beaa9d5ade4926ef231e3ec9d0a517fe93830e90` deployed; named user service `codex-control-plane.service` restarted. Live health, source fingerprint and all 38 release files agree. Schema remains 28; verified private backup and previous release are preserved.
- Windows `web-mcp-assistant`: unpacked r4 candidate activated through the supported full-clean lifecycle. At 15:40:27.992 +07, epoch `activation-mv3kgpod-d9dec64ec4eeeffe5f6e764313648af5` remains READY with admission open, all aggregate readiness flags true and update incomplete false. Host 6388, UI 4784, Coding MCP 28604 and connected agent 18876 have matching process identities; agent iteration 41 completed with heartbeat succeeded. Coding MCP running/disk revision agrees across 148 files.
- New authenticated central MCP proof completed with exit 0. Inventory reports the exact binding online/ready/dispatchable with policy enabled. A wrong facade pin returns model-visible `CONTRACT_MISMATCH`, fixed field diagnostics and current expected pin, with execution not started. It no longer collapses into JSON-RPC Invalid params.
- Historical patch rejection exposes its safe pre-effect reason without replay. New read `act_c8412bf197ee427fb9a983ad0bd19ab2` returns the expected 49-byte fixture and hash. New read `act_a600a322c7cc4dbf95c2c66b055820e4` returns the first 40 source lines, 1,366 bytes, of `control-plane/control_plane/mcp_facade.py`; digest verification passes.
- Facade pin must come from current inventory/discovery. The user's `workspace_context` profile and node hash were the wrong pin. `task_id` is optional for that bounded read; the original source path lacked its `control-plane/` parent.

## Scope, job state and preservation

Exact binding `bind_3e05bf64cb3e4bab93d930ae1692bebb` retains Tools-Codex-web on DaoChienThang. Context/pilot and Windows metadata assignment expire at **16:26:24.008 +07 on 2026-10-11**. Standing read/write policies remain enabled. The metadata assignment reports `windows_acl_verified=false`; no independent renewed-assignment ACL proof is claimed.

The supported admission census last verified zero active command/background/managed-process/agent-lane counts, 17 classified stale candidates and one pending RUN `95e909f0040a448faa9f1f3257e2ee2c`, WAVE `c101beadfc6d4f2fbc13845052c84693`. Its acceptance is deliberately preserved. No manual ledger edit, proof fabrication or hidden authority transfer occurred. The bounded connected agent remains active for the authorized scope; it has 200 iterations with 15-second interval, not a permanent supervisor. Both new reads reached completed receipt states.

Final Ubuntu read-only observation at 15:40:15.669 +07 confirms the unchanged release/service identity, current ready/enabled node heartbeat, exact context/pilot expiry and both new actions settled/completed. Server counts are 30 actions, 4 task sessions and 1 acceptance, with zero queued/accepted actions, open writer leases or open tasks. All 13 historical unresolved rows retain their exact digest. The observer's initial overly strict context-uniqueness assertion was corrected to allow same-binding bounded per-action contexts; its failed observation remains evidence and made no server mutation. The final observation sees only the standing context live.

No new live patch roundtrip was run. The exact-file patch lane requires an existing file, and a forward/revert pair would create two new local ACCEPTING waves. The missing central-to-local semantic acceptance adapter would leave those waves pending. Existing write-policy/focused proof and earlier live patch evidence remain separate from a new r4 write claim. Thirteen historical unresolved actions remain preserved without replay.

## Validation and failure classification

Focused source proof: 88 distinct checks PASS, one real symlink check SKIP for Windows creation privileges; reparse-attribute denial PASS. The real-process HTTP exec E2E was not run. r4 packaged smoke passed after one unchanged retry; the initial startup timeout is retained.

Two canonical ledger census attempts exceeded the existing 30-second deadline. Content-free timing located sequential contextual projection I/O; snapshot/integrity/hash took 4.672 seconds, 1,083 context projections completed at 19.875 seconds. A subsequent normal census passed in 6.63 seconds and one supported refresh reached READY. No deadline increase, gate bypass or speculative source optimization was applied.

Primary `npm run check:coding-tools-history` and its repository secret guard PASS (4,985 evidence files at that observation); the history guard alone passed again after final metadata creation with 4,987 files. Diff whitespace checks PASS, no unmerged index entries and no staged changes. Newly added sanitized checkpoint metadata is preserved under `.coding-tools`; no delivery staging is performed because there is no primary commit or push.

## Remaining gate and exact next action

Command execution remains blocked by `WINDOWS_SANDBOX_NOT_READY`: Sandbox feature was enabled with restart required, but `WindowsSandbox.exe` is absent and local exec policy is not installed. The host E-drive root/cwd realpath probe passes; the historical EPERM originated in the ProcessContainer fallback and does not prove lost host filesystem access.

The owner must restart Windows when ready. After that, inspect fresh authority/runtime state, prove Sandbox ready, install the supported local command policy for the exact workspace, and run one allowed command/test with bounded verified output. Expired context/pilot is not automatically renewed. No Windows restart occurred in this rollout.

Actual ChatGPT client discovery/acceptance, new r4 live write, artifact acceptance and local semantic completion remain unproven. Directory listing and the central-to-local acceptance adapter remain separate source work. Do not present deployed/READY/read proof as complete command or production acceptance.

## Changed resources and operations

This continuation activated the prepared Windows candidate, installed matching metadata authority, renewed Ubuntu context/pilot through supported APIs, deployed the authorized Ubuntu revision and restarted its named service. It updated the current MCP-Web section of `docs/CURRENT_STATE.md`, `docs/MCP_WEB_OPERATIONS.md` and sanitized rollout evidence. Primary commit, push, public release and Windows reboot did not occur.

Evidence: `ubuntu-rollout-checkpoint.md`, `ubuntu-deployment-result.jsonl`, `ubuntu-authority-renewal.jsonl`, `ubuntu-final-observation.jsonl`, `windows-activation-checkpoint.md`, `windows-activation.jsonl`, `live-rollout-verification.jsonl`, `validation-checkpoint.md`, and `windows-candidate.json` in this directory.
