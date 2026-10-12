# Initial verification server adapter: local artifact

Prepared from dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f` on 2026-10-11. This packet proves source behavior and local artifact integrity. It is not deployed runtime, an executed native check, or native semantic acceptance.

## Frozen release

- Source revision: `9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c` (content identity, not a Git commit).
- Package fingerprint: `sha256:80a2e82115714f8e5e32cc7144e180b1f83ee8738e2af1e4821de8048128f7e8`.
- Archive SHA-256: `7d1a0b015208b4fc257a52bc888cd8a15f559ce33cf04846953d533002b7c273`.
- Release-manifest SHA-256: `a9ecac2d8935cd36790ee08a49be090446a2458a10d7a4bf542f825e34e14e55`.
- Existing release format: 38 payload files plus the manifest. Only `mcp_facade.py`, `store.py`, `node_agent.py`, and `recovery_approved_patch_bridge.cjs` differ from frozen Store395. The other 34 payload files, deployment scripts and bundled documentation retain their original bytes.
- `packet-manifest.json` pins original Store395, every raw Windows source hash and normalized LF payload hash, migration/rollback requirements, and local verifier result. The preparation helper is immutable and refuses to replace an existing packet.

The expected old service identity `cp_6766892f5ada47d1862a0d24334f1116` is copied from the prior reviewed deployment record. This lane did not query or change the live service. Store395 remains the last deployed source identity known to this lane.

## Contract

The optional CP `verification` object has exactly four required keys: `argv`, `cwd`, `timeout_ms`, `max_output_bytes`. No default command or coercion is introduced. Existing CP exec bounds apply: 1–8 argv items, each at most 256 UTF-8 bytes, bare executable, no shell metacharacters or ASCII controls; empty or strict root-relative cwd of at most 512 UTF-8 bytes; integer timeout 5000–300000 ms and output 1024–65536 bytes. These are the narrower outer CP bounds around the native adapter.

Permission, intent, action and idempotency identity seal the exact plan. Reviewed-plan drift or omission after a reviewed plan is rejected. Missing plans remain omitted from immutable legacy digests. Central exec enablement and write scope, advertised exec/write capabilities, both local policies, exact registered target, allowlist, limits and expiry are required before the node writes its prepared journal boundary. The node's synthetic exec request is validation only; it is never dispatched and never substitutes the approved-patch actor.

The optional returned `initial_verification` summary is exactly `plan_sha256`, `proof_status`, `proof_ids`, `proof_fingerprint`, with an optional paired `command_id`/`job_id`. Passed proof requires nonempty hex32 IDs and a hex64 fingerprint. Failed/timed-out proof permits empty IDs and requires a null fingerprint. The response hash seals `{file, initial_verification}`; legacy no-plan responses continue to hash `file` alone.

An applied patch with failed/timed-out proof keeps a completed exact effect receipt and its RUN/WAVE. Semantic acceptance remains pending. UNKNOWN, crash recovery, receipt dedup and idempotency do not replay either the patch or initial check. Python subprocess and Recovery IPC allow the command timeout plus 300000 ms for Sandbox setup/observation, capped at 600000 ms by plan validation. This does not increase the command's own timeout.

## Focused proof

31 distinct Python test cases and 3 CJS cases succeeded across the following commands. Two new test-fixture errors (wrong error-response nesting and missing lifecycle fields) and a new integration-fixture missing installer argument were repaired; their targeted retries passed. These were fixture defects, not remaining product failures. No live Windows check was launched.

```powershell
# From E:\Github\Tools-Codex-web\control-plane
python -m unittest tests.test_initial_verification_facade tests.test_mcp_permission_requests tests.test_approved_patch_node_agent
python -m unittest tests.test_initial_verification_facade
python -m unittest tests.test_mcp_approved_patch_http_node_e2e.McpApprovedPatchHttpNodeE2ETests.test_standing_initial_verification_is_immutable_and_failed_proof_preserves_one_effect tests.test_mcp_approved_patch_http_node_e2e.McpApprovedPatchHttpNodeE2ETests.test_oauth_permission_to_node_patch_to_verified_status
python -m unittest tests.test_mcp_approved_patch_http_node_e2e.McpApprovedPatchHttpNodeE2ETests.test_standing_initial_verification_is_immutable_and_failed_proof_preserves_one_effect
python -m unittest tests.test_mcp_permission_requests.McpPermissionRequestTests.test_v28_initial_verification_columns_preserve_legacy_history_and_immutable_digests

# From E:\Github\Tools-Codex-web
node --test control-plane/tests/recovery_approved_patch_bridge.test.cjs
```

The schema28 migration test removes only the new columns in a temporary fixture, reopens it with schema29, and compares all original permission, intent, action, context, work-request and event fields unchanged. It computes the original no-plan immutable intent digest independently and proves that replay retains the same hash and action after migration.

The packet helper compiled the three frozen Python payloads and ran the original frozen `control-plane-verify-release.py` verifier locally. `git diff --check` passed for the edited source/test files. The CJS test exercises exact request forwarding, bounded IPC grace, unchanged actor, failed proof and pending acceptance.

## Migration and rollback

Schema29 adds nullable `verification_json TEXT` to the three existing patch permission/intent tables. It creates no new table and does not rewrite legacy history. It updates SQLite `user_version` from28 to29.

Store395/schema28 rejects a schema29 database. After schema29 first opens the live database, changing only the release symlink back to Store395 is insufficient. Preserve the old release and a transactionally consistent preactivation backup; retain all postmigration task history. Use a schema29-compatible rollback or a forward fix. Do not silently lower `user_version` or restore an old database snapshot over subsequent actions/receipts.

Future deployment must separately verify its authorized destination, current source/service identities, quiescent task/writer/action state, fresh backup integrity, source/package pins and bounded authority. This lane performed no SSH, deployment, service operation, authority change, database restore, commit, push, tag or release publication. Windows/native source and packaged acceptance remain separate root work.
