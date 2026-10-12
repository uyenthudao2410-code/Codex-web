# r11 lifecycle checkpoint — 12 October 2026 (+07)

This directory is append-only operational evidence. Frozen helpers and attempt receipts remain intact. No helper in this lane was used to accept historical work or change product source.

## Observed chronology

| Time (+07) | Observation |
| --- | --- |
| 00:00–00:02 | Previously verified host 25548, agent 26860, native 12688 and Recovery MCP 19528 were absent. The profile descriptor still identified host 25548. |
| 00:07 | Original WMI attempt was reserved and returned a generic refusal without a PID. Its generic receipt does not prove the failing stage; root reconciled the unchanged descriptor and absent target processes. |
| 00:12 | Separately reserved diagnostic stopped at `package_hash`, `CommandNotFoundException`, with `create_invoked=false`, `create_returned=false`, PID null. The Node child inherited a PowerShell module path incompatible with Windows PowerShell 5.1; `Get-FileHash` was unavailable. |
| 00:14–00:15 | A distinct, root-directed attempt used the native Windows PowerShell module directory, an explicit CimCmdlets import and .NET hashing. WMI `Create` returned 0 and PID 17272. The helper then refused its overly strict requirement that the child belong to no Windows Job. No second host was launched and the child was not killed. |
| 00:17 | Read-only reconciliation proved PID 17272 / token `134362124992663030` / instance `32d052d8c746b30f3f081c850021216e`, exact package path and user, parent WmiPrvSE 26876, and authenticated IPC. It remained alive after the launching tool session ended. Job membership was observed; the Job identity and durable supervisor independence were not proven. The package matched all 12 pinned source files and canonical active work counts were zero. |
| 00:16–00:18 | One supported `runtime.start` request returned `UPDATE_INCOMPLETE`. Source inspection showed that replacing a dead native MCP under a terminal READY epoch is deliberately refused. Valid persisted READY adoption does not authorize a new MCP process under that epoch. |
| 00:19 | Root issued one supported `full_clean_refresh`, with no source checkpoint and historical acceptance pending preserved. It reached HANDOFF and created a replacement epoch. |
| 00:20:20 | Root's read-only receipt observed host 20400 / token `134362127609947980` / instance `e289f4d07ed2d9d2fb1d49d7d66b599e`. Epoch `activation-mv438ehi-cebe9d7cb6af824eb7153869dc4435bb` projected `UPDATE_INCOMPLETE`, admission closed. Native `i9NiVIv9hFBben2i` / `doSwkyBa0xMXFRM4` reported `mcp_ready=true`, `identity_current=false`. All four readiness fields were false. This is the last root status bound by the checkpoint receipt, not a claim of READY. |
| 00:22:09.910 | The approved 60-minute window expired. No connected agent was launched, no second canary was dispatched, and no acceptance occurred. |
| 00:23:15 | Query-only checkpoint preserved the historical RUN/WAVE hashes and unchanged canary preimage. Source parity was now 11/12 because the separately authorized source wave had begun changing `control-plane/control_plane/node_agent.py`. The earlier 12/12 operational proof remains historical; it is not proof that the newly edited source matches r11. |

## Proof and current limit

`checkpoint-1791739395612.json` (SHA-256 `60c750d3ceef4492f434f5bca2c9fc7cce5832673224970e699c692d5a78eca3`) binds the public receipts, old ledger row hashes, canary preimage, source comparison and latest root status. Original launcher and diagnostic files were preserved. Node syntax and PowerShell parsing passed. A Node-to-Windows-PowerShell dry run with native module paths passed through `Invoke-CimMethod -WhatIf`; it created no process.

The frozen connected-agent helper was prepared but not executed. Requiring final native identity before launching the agent is circular during central activation: the supported, scoped connected-agent bootstrap must run before final central READY. Repair that bootstrap order while preserving the native identity gate for code execution. Complete the new source wave, build a matching candidate, then activate and verify it under a fresh authorized runtime window.

No commit, push, tag, release, Ubuntu deployment/restart, Windows reboot, new persistent service/task, historical acceptance mutation or VM termination was performed by this lane. Root did perform the same-candidate Windows host launch and supported refresh described above. Genuine native ChatWeb final acceptance remains unproven.
