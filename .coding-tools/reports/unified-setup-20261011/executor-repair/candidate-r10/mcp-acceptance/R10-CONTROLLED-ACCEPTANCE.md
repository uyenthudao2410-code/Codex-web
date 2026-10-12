# r10 controlled live acceptance checkpoint

Observation window: 2026-10-11, final checkpoint **20:38:26.304 +07**. Repository dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`. This records root's completed controlled rollout and live MCP execution evidence; it is not a signed public release or patch semantic acceptance.

## Operated package and readiness

Candidate `windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked` operates `web-mcp-assistant` on DaoChienThang. Its source/package parity covers 11 changed source files, four unchanged critical/native resources and seven unchanged UI files. At the final checkpoint:

- Epoch `activation-mv3v3pus-8547a1b4205f606ae6211c793f9ec8b2`: READY, admission open, update incomplete false.
- Host PID 25868, UI 26252, native 17488 and bounded agent 25208: exact live process/start-token identities.
- Local, central, authority and fully-ready flags: all true.
- MCP discovery at 20:37:41: exact target online/ready/enabled.
- Package app.asar SHA `c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9`; executable SHA `6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f`.

Ubuntu `svhome@100.116.112.22` serves Store snapshot `395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5`, package `sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419`, service instance `cp_6766892f5ada47d1862a0d24334f1116`.

Approved recovery close revoked the original pilot. The supported same-expiry replacement `pilot_0b07c86e179a4a6182b8503faa66dfaa` reopened intake against the real recovered epoch, retaining context `ctx_9e58c758a20249479b6ec806970f68ca`, service grant, binding and exact Tools-Codex-web folder. The authority window remains **19:48:18.491–20:48:18.491 +07**; no renewal or widening occurred during recovery.

## Live command results

Both recovered-epoch submissions ran the exact structured invocation `node --test tests/control-plane-approved-patch-runtime.test.js` through MCP, with one delivery attempt each.

| Submission | Action / task | Durable Job | Result |
| --- | --- | --- | --- |
| Initial, transport mode `cold`, 20:35:13 | `act_91aaaf5601124cb19c6eff321112e09d` / `task_7858f9ecc00c4bb583062680be7f6a06` | `db555fd7c8b44ca4957b8e842dcffe9d` | 4 PASS, 0 FAIL, exit 0; terminal exited, no timeout |
| Distinct warm, 20:36:49 | `act_851da1bd59764e24bb5fa50d11c102f6` / `task_90a138b2a6e344a1837354fb46d5c388` | `ee1ebaad7bd44883ad5deba4c203ea91` | 4 PASS, 0 FAIL, exit 0; terminal exited, no timeout |

Root executed verifier v3 and observed PASS for both immutable transports, submitted journal receipts and exact durable Job/native identities. The already-executed outcomes are retained in `root-witnessed-job-correlations.json`, explicitly typed as `root_tool_observation_summary`, not a raw stdout capture. Response/output hashes were recomputed internally; raw stdout/stderr and protected journal/config were not published. Trial tasks, temporary action contexts and writers were closed; retained history was preserved. Neither command was replayed. The original first r10 cold action `act_9482be2aef814d82b3ff4722b5979a25` also passed verifier v2 after its schema-location correction; its original KeyError evidence remains preserved.

The initial preflight at 20:34:05 saw zero Sandbox/backend processes but a stale regular private daemon record. `cold_candidate_observed=false`; that record was neither read nor hashed. Therefore transport mode `cold` describes its intended sequence, **not verified fresh cold startup**. The 20:36:25 warm observation saw three Sandbox processes and a daemon, with `warm_candidate_observed=true`; manager ownership/lease, executor reuse and cleanup remained false/unproven. Neither host hint establishes VM cleanup. No timeout canary was submitted.

## Final state and preserved work

Query-only final census at 20:38:25.587 records SQLite integrity `ok`, zero active tool calls, commands, starting commands, background operations, managed processes and agent lanes; no unexplained live run, unbound residue or projection drift. It classifies `safe=false / RUNTIME_BUSY` solely for the expected `live_runtime_state_process`, which the existing live-runtime observation guard explicitly admits. This is not a claim that the complete runtime is stopped or VM resources have been cleaned.

Pending acceptance is unchanged:

- RUN `95e909f0040a448faa9f1f3257e2ee2c`, record SHA `a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590`.
- WAVE `c101beadfc6d4f2fbc13845052c84693`, record SHA `59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce`.

The new exec Jobs and payloads have empty equal RUN/WAVE. They prove real standalone execution and output correlation; they do **not** provide source-bound proof for a patch RUN/WAVE or controller semantic acceptance.

## Recovery event and remaining gates

The first r10 runtime process set disappeared abruptly around 20:17. Cause remains unresolved. Read-only parent Job membership observations are membership evidence, not causation. Supported recovery restored the same package with a fresh native epoch and actual ready heartbeat; no fake readiness, Windows reboot, old command replay or legacy pending acceptance occurred.

Remaining work: one NEW approved patch carrying admitted structured initial verification into its native ProofLedger, post-effect proof failure/dedup observation, then genuine lifecycle-attested ChatWeb `task_control accept`; durable managed agent/private delegation; cleanup and timeout evidence; actual ChatGPT workflow/renderer continuation and signed/reproducible installer gate. Source work may continue while packaged runtime remains r10. The r10 11-file parity is the pre-adapter snapshot; initial-proof changes need new focused validation and candidate parity/controlled rollout before being described as packaged or live.

Store deployment and Ubuntu service restart occurred earlier under explicit approval. Git remains dirty `main @ 2c554f59`; no commit, push, tag, public release or Windows reboot occurred. This documentation lane only updated maintained docs and added this report/manifest; no source/helper/runtime/authority modification or repeated test occurred.

## Retained evidence

Exact artifact paths, byte lengths, SHA-256 values and timestamped row selections are captured in `R10-CONTROLLED-ACCEPTANCE.receipts.json`. Primary receipts include:

- `transport-execute-cold-20261011T133513484505Z.jsonl`: `378918499ef5d8aedb9fa9b47f9b3827b46e9e514a00f4253aa5a6f33277d239`.
- `transport-execute-warm-20261011T133649546404Z.jsonl`: `312a5ad1bca4066aa12039f836fb35acff7662aae9ed1eb8d70c339f71967920`.
- `../activation/server-recovery-reopened.json`: `40e3a076fd0bc3a81663576e8e577286b52730414d6f2fb8016d6e562294f0ed`.
- `../activation/windows-trial-recovery.jsonl`: observed snapshot SHA `1931fda594528a5d0dfb4c9e823f731b410ea3f04ee0f874ec6102af3c18ce3b`, final proof row 20:38:26.304 +07. This append-only journal may subsequently grow; preserve the receipt selection and capture hash/window rather than rewriting it.
