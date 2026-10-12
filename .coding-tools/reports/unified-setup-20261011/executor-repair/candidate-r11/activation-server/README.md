# r11 Ubuntu activation helpers

Prepared locally for root to execute under the user's r11 rollout and exact-scope 60-minute approval. This lane did not perform SSH, deployment, restart, policy installation, or authority mutation.

## Frozen pins

| Item | SHA256 |
| --- | --- |
| `helper-manifest.json` | `d764e36dbbabdfb8f3b5202b95f108e90b43bbf2aed0682be19aed10b734c95e` |
| `root-ssh.py` | `d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba` |
| `r11_common.py` | `c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f` |
| `ubuntu-r11-authority.py` | `16185e4b36ce415ea3fbddc2c6c396a6822c6afe8bee40942d21ff2094ece760` |
| `ubuntu-r11-rollout.py` | `3a453738d7f9194c1da29b1da8c21dbfd0f53cf658bd0ca906e979d765ed5385` |
| `ubuntu-r11-recovery.py` | `329422e156165be0bdb45b431e763f0fda164b4a65a47495d8eb0887dabea712` |

Both archive pins are recorded in the manifest. Original target: Store395/schema28. Approved main: `9cae1044…`/schema29. Emergency recovery: `81303f7c…`/schema29 with permanently closed intake. Source revisions are content-addressed release snapshots, not Git commits.

## Root usage

Set `$driver` to the absolute local path of `root-ssh.py`. All actions below run only when root invokes them. `stage` transfers bytes; other actions are read-only unless `--execute` is included.

```powershell
python -B $driver stage
python -B $driver observe --remote-dir <returned_remote_dir>
python -B $driver close --remote-dir <dir> --execute --expected-service-instance <fresh_service_id> --expected-state-sha256 <fresh_state_sha> --expected-grant-sha256 <fresh_grant_sha> --observed-at-ms <fresh_observed_ms>
```

The transport stages all four helpers and both archives in a new protected `incoming/r11-approved-<timestamp>` directory, refusing overwrite. Archives are read from that exact directory; nothing is silently copied into the global incoming path. SSH uses BatchMode and strict host-key verification. Fixed argument arrays are shell-quoted with `shlex.join`. Stderr is captured and never disclosed or persisted. Successful and failed JSON public receipts are written exclusively under `remote-receipts/`.

After the closed-intake receipt, root may perform the separately prepared Windows cleanup. Before each server mutation, call `observe` again and use that result's four fresh pin values (service instance, state SHA, grant SHA, observed timestamp). Observations must be less than 60 seconds old.

```powershell
python -B $driver deploy --remote-dir <dir> --execute <four_fresh_pin_flags>
python -B $driver observe --remote-dir <dir>
python -B $driver renew --remote-dir <dir> --execute <four_fresh_pin_flags>
```

Deployment verifies Store395 release/config/service identity, the exact historical fence and quiescent state; takes and independently inspects a transactional SQLite backup; stages/verifies both releases; applies the maintained activation helper; switches current and restarts only `svhome`'s `codex-control-plane.service`. The final state must be schema29, a new service instance, intake `recovery`, unchanged execution/permission/task/context history, and unchanged service grant. It does not renew authority or open intake.

Renewal starts one new 60-minute window only after successful r11 deployment. It closes old contexts for the exact binding, creates/reuses one exact context and pilot, preserves the existing service grant/scopes, and returns `policy_assignment`. Retrying uses the same anchored expiry and never extends the window or creates duplicates. No stale r10 operation marker is reanchored.

Root applies the returned policy assignment to exactly `E:\Github\Tools-Codex-web`, profile `web-mcp-assistant`, device/workspace/generation in the manifest, then activates r11 Windows. After a fresh exact r11 heartbeat and a new `observe`:

```powershell
python -B $driver reopen --remote-dir <dir> --execute <four_fresh_pin_flags> --expected-activation-epoch <r11_epoch> --expected-runtime-instance <r11_runtime_id> --expected-mcp-instance <r11_mcp_id> --expected-contract-version <r11_contract>
```

Reopening requires exact supplied node identities, heartbeat under 60 seconds old, `readiness=ready`, enabled policy with expiry exactly equal to the anchored authority window, the exact context/pilot, and the unchanged grant. It opens only `scoped_pilot`.

## Emergency path

Deployment failures report the exact reached phase and keep intake closed. There is no automatic schema28 fallback and no database restore. The approved emergency release is staged before switching main. Its activation is a separate explicit root action:

```powershell
python -B $driver recovery-observe --remote-dir <dir>
python -B $driver recover --remote-dir <dir> --execute --expected-state-sha256 <fresh_state_sha> --observed-at-ms <fresh_observed_ms> --expected-current-link <fresh_exact_link>
```

This emergency driver supports only exact r11 current/config with the existing schema29 database already in persisted recovery. It takes a new schema29 backup, activates schema29-compatible observation/receipt recovery, and preserves all history. It never grants authority, resumes verification, lowers `user_version`, or restores an old snapshot. Partial configuration states outside those guards require root to inspect and reconcile the exact service/config/current state first.

## Evidence and state

`proof-receipt.json`: 5 offline checks passed, including schema28→29 normalized history fingerprints, exact 60-minute retry safety, wrong-target rejection, and private stdout rejection. `transport-smoke-receipt.json`: mocked SSH proves binary staging of all helpers/archives, strict hostcheck, argument roundtrip, immutable receipts, and no stderr disclosure. These are local helper proofs, not live deployment evidence.

Git remains dirty `main` at the observed `2c554f59…`; unrelated work and frozen prior reports are preserved. No live RUN/WAVE/Job was created or queried by this lane. Root owns all external mutations, live receipts, and final acceptance.
