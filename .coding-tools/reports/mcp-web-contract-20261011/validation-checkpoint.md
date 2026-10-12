# MCP web feedback — source validation checkpoint

Observation date: 2026-10-11, Asia/Saigon. Primary repository: `E:/Github/Tools-Codex-web`, dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`. Earlier changes are preserved. This report records focused source proof and preparation, not production acceptance.

## Reproduction and diagnosis

`live-baseline.jsonl` captures live discovery/inventory around 14:52 +07 and one bounded fixture read. The reported profile `workspace_context` and hash `bc44c044...` are not the Ubuntu facade contract. Reproducing that pin returned JSON-RPC `-32602`, inner `CONTRACT_MISMATCH`. Using the discovery pin returned verified read receipt for action `act_c16e0a69c23d42afbfeb514664572703`, 49 bytes, SHA-256 `14c82d572e3416dc67c06046ed33455ccfbaee4af1b1160196d97083def600a2`.

`task_id` is optional for this bounded read. The source path from this workspace root is `control-plane/control_plane/mcp_facade.py`; the submitted `control_plane/mcp_facade.py` misses its parent directory. The live read proof above concerns the known fixture, not a successful live read of the source file.

Live discovery already advertised exec_run/exec_status and exec_output/exec_stop. The web feedback claiming no relay differs from this observation; stale/different client discovery is an inference, not a demonstrated client refresh. Registration `exec=true` does not prove local exec admission.

Historical action `act_16f5443e532942019fa7bb43868b34b0` was rejected before effect because the old bridge sent unsupported `include_diff`. Existing `../folder-permissions-20261011/pre-effect-rejection.json` and `terminal-reconciliation-receipt.json` bind the terminalized worker, unchanged preimage and rejected receipt. That action has already been reconciled; it was not retried here.

## Source changes

- Facade inventory returns the copyable facade pin, relay operations and root-relative POSIX path format.
- Recognized tool argument/domain failures return MCP `result.isError=true`, typed code, fixed field diagnostics and recovery instruction. Malformed protocol/non-object arguments/unknown tools remain JSON-RPC errors. Offending values and arbitrary keys are not reflected.
- Non-string operation values, including JSON arrays/objects/null, are rejected before set-based dispatch.
- Terminal rejected/failed/stopped status exposes sanitized receipt reasons. UNKNOWN remains reconciliation-required. Failed/stopped patch effects remain unverified/nullable.
- A central owner verdict is reported separately from the pending local RUN/WAVE semantic acceptance.
- Artifact reads enforce request/policy expiry, exact target/tool, policy bytes/lines, regular-file bounded handle reads, reparse/target-drift checks and authority recheck before relay. WebP requires RIFF and WEBP at their canonical offsets.
- Writer regression now advances time and verifies the renewed lease still fences another writer after the original expiry.

Input tool schemas/descriptors, facade pinning, authentication, permissions and sandbox gates are preserved. No new directory-listing operation or semantic-acceptance authority was added.

## Focused verification

Commands use `python -W error -B -m unittest discover -s tests -p <file> -v` from `control-plane`. Prior successful checks are reused where later changes do not alter the checked behavior; final argument-type/path changes reran the feedback suite. The writer and wrong-root fixtures were rerun individually after their final edits.

| Check | Result |
| --- | --- |
| MCP client feedback | 10 PASS |
| Bounded read facade | 4 PASS |
| Affected OAuth HTTP tool failures | 4 PASS |
| Exec facade | 8 PASS |
| Permission requests | 10 PASS |
| Task sessions | 13 PASS; final renewal case rerun PASS |
| Private service facade | 10 PASS |
| Terminal failure helper | 9 PASS |
| Public terminal status/central verdict | 4 PASS |
| Artifact relay/magic/digest | 3 PASS |
| Artifact node admission/limits/drift | 11 PASS, 1 SKIP |
| Existing standing-artifact fixture | 1 PASS |
| Existing wrong-root artifact fixture with valid admission fields | 1 PASS |

88 distinct checks passed; one actual file-symlink fixture was skipped because this Windows host lacks creation privileges. The Windows reparse-attribute denial test passed. The malformed older wrong-root fixture initially failed at the newly enforced expiry/tool gate; adding valid admission fields restored the intended target-mismatch assertion. No meaningful validation was weakened.

The real-process HTTP exec E2E was not run; only its affected error assertions were updated. The Windows sandbox remains unproven before owner reboot, so these tests do not establish live command execution.

## Delivery and remaining gates

Frozen source identities are recorded in `frozen-source-inputs.json`. Candidate archive/hash/isolated revision and Windows unpacked smoke are recorded separately in `artifact-receipt.json` and `windows-candidate.json` when preparation completes. The Ubuntu candidate starts from deployed `70de202d` and changes only facade, node agent, new status helper and generated deployment documentation in its release manifest. Primary HEAD/index are preserved.

No new deployment, service operation, runtime activation, permission renewal, Windows reboot, push or public release is performed in this source-repair wave. The bounded live fixture read was the only new workspace action. Final job observations are recorded in `final-local-state.json`.

Windows candidate preparation completed at `dist/windows-candidate-mxc-wsb-cbe1774-mcp-feedback-1011-r4/win-unpacked`. Source/bundled node SHA-256 is `3f044fd7883412c54d58fb54755d54dd133810ec0687c32efc6a41f96c23e8c2`. Electron asar SHA-256 is `52a267375bd449c2f2f630814a1fc6382dd683fe8948fa2dd2728dacf1df365a`, identical to running r3. First isolated smoke failed its startup deadline (`PACKAGED_USER_DATA_ISOLATION_FAILED:child_alive=true`); one unchanged retry passed, including the eight-tool smart-v3 surface and Recovery/descriptor/process cleanup checks. Production descriptor was preserved. The new candidate is not active, and smoke does not establish remote artifact or live exec success.

Final local census uses an immutable query-only ledger snapshot: 1 AWAITING_ACCEPTANCE run, 17 stale candidates, no unexplained runs or unbound resource residues. Resource-specific active counts were not exposed by this summary and remain unknown; this is not proof of an empty OS process set. The prior connected agent, Recovery Host and UI were observed present with matching recorded identities. The canonical ledger was not modified by the observation.

Primary `npm run check:coding-tools-history` passed (4953 evidence files at that check) and repository secret guard passed. New candidate preparation receipts are retained under this evidence directory; final metadata/history verification follows their creation.

Ubuntu preparation completed: isolated revision `beaa9d5ade4926ef231e3ec9d0a517fe93830e90`, exact parent `70de202d93c9a759befe5d38491ce54e9ef4b3cd`, branch `codex/mcp-web-client-feedback`. Archive SHA-256 `e31132a545da55cad564a373c138bb644917c8cbce73e87b724c88dfee6f3b36`; package fingerprint `sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835`. Mandatory isolated delivery stage/check, strict builder and verifier passed. Database schema stays 28; manifest has 38 files, 34 unchanged from the deployed package. All 16 frozen source/test inputs still match after build. Isolated checkout is clean; primary remains dirty main at the recorded HEAD with empty staged diff and unchanged index. Artifact preparation jobs completed; neither candidate is active.

Final primary whitespace/unmerged checks passed. History guard passed again with 4965 evidence files after candidate receipts/archive creation. Operator rollout is specified in `rollout-review.md`; no authorization is inferred from these preparation proofs.

Open gates: authorize the prepared Ubuntu revision and Windows candidate activation; refresh the web client's discovery; owner reboot Windows, then separately prove sandbox readiness/local exec policy/allowed command; retain pending local acceptance until a supported controller/adapter completes it; reconcile historical UNKNOWN actions through supported evidence. Scope expiry is 15:11:19 +07 on 2026-10-11; elapsed time does not renew authority.
