# r11 standing policy observation reconciliation

This sibling bundle preserves the frozen `../activation-server` bundle and its live receipts. Root owns SSH, staging, intake operations, and final acceptance. Preparation performed no external operation.

## Exact correction

`node_agent.py` emits `expires_at_ms = observation_time + 60000` for an admitted standing policy (`_standing_policy_observation`, lines 1420–1499). `read_only_policy_observation` prefers that standing telemetry (lines 2219–2222). The heartbeat field reports observation freshness; the anchored context/pilot expiration independently limits this verification window.

Only the derivative `ubuntu-r11-authority.py` reopen guard changes. It requires enabled policy telemetry with integer expiry strictly after the fresh overview and no later than node `last_seen_at_ms + 60000`. It retains the fresh ready heartbeat, all four exact supplied runtime identities, quiescent history/grant pins, service instance, and existing marker checks. Byte-identical `r11_common.py::renewed_authority` still requires exactly one correct context and pilot at the unchanged anchored 60-minute expiry. No expiry, marker, service grant, server product source, or candidate payload is changed by preparation.

## Pins

| Item | SHA256 |
| --- | --- |
| `helper-manifest.json` | `8081bb3aa9cc9de9978e7afb7b739fae9fb2de2c775c30890b7c030ebf81da66` |
| `ubuntu-r11-authority.py` | `5ebb015298ba0442599af08ae31909fbb0af04294e1c95036455f8819d3743fd` |
| `root-ssh.py` | `d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba` |
| `r11_common.py` | `c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f` |
| `ubuntu-r11-rollout.py` | `3a453738d7f9194c1da29b1da8c21dbfd0f53cf658bd0ca906e979d765ed5385` |
| `ubuntu-r11-recovery.py` | `329422e156165be0bdb45b431e763f0fda164b4a65a47495d8eb0887dabea712` |

The transport, common, rollout, and recovery files are byte copies. Approved release and recovery archive pins are unchanged and bound in the new manifest, which also binds the parent manifest and original authority helper hash.

## Root next action

Set `$driver` to this directory's absolute `root-ssh.py` path. Stage in a new protected directory, obtain a fresh observation, then reopen with those exact pins and the current r11 epoch/runtime/MCP/contract identities. Preserve the existing authority window **22:03:16–23:03:16 +07, October 11, 2026** (`expires_at_ms=1791734596302`). Do not run `renew`, `close`, `deploy`, or recovery as part of this reconciliation.

```powershell
python -B $driver stage
python -B $driver observe --remote-dir <new_remote_dir>
python -B $driver reopen --remote-dir <new_remote_dir> --execute --expected-service-instance <fresh_service_id> --expected-state-sha256 <fresh_state_sha> --expected-grant-sha256 <fresh_grant_sha> --observed-at-ms <fresh_observed_ms> --expected-activation-epoch <r11_epoch> --expected-runtime-instance <r11_runtime_id> --expected-mcp-instance <r11_mcp_id> --expected-contract-version <r11_contract>
```

`prove-policy-observation.py` is a local proof script; its receipt exercises the actual derivative guard AST and unchanged authority validator without importing live product state or making network calls. Positive standing TTL and negative expired TTL/context/pilot, incorrect identity/window, and TTL boundaries are covered.

Git remains dirty `main` at `2c554f59cb7b8ffc86ce5e0e28076c792777642f`. Pending RUN/WAVE acceptance and live jobs are owned by root and unchanged by this preparation. No commit, push, release, deployment, service operation, or policy mutation occurred in this lane.
