# Approved r7 Windows activation helper

Target: DaoChienThang, `C:/Users/daoth/AppData/Roaming/web-mcp-assistant`,
`E:/Github/Tools-Codex-web`. The helper pins the original r5 host/UI/agent process
start tokens, verifies r5/r7 package hashes, and binds its six imported service
modules to the r7 archive. It never edits semantic acceptance or the ledger.

Run from the repository root with Node. Root owns all mutations.

```powershell
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs preflight
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs activate --operator-approved
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs status
```

Activate/rollback require `authorization.md` and an exact server intake-closed
receipt less than ten minutes old. Activation stops only proven old process
identities, takes an exclusive read-only canonical census after native stop,
preserves the exact pending acceptance run, launches r7, and releases the gate.
Initial launch evidence is distinct from UI registration and readiness; observe
`status` after registration before proceeding or considering rollback.

After server same-scope renewal, root verifies no new queued/accepted actions,
open tasks or writers, then executes:

```powershell
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs policy --operator-approved
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs refresh --operator-approved
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs agent --operator-approved
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs status
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs proof
```

Those mutations require the exact approved, unexpired one-hour renewal receipt.
The policy phase syncs metadata expiry, retains current standing file/exec
policies, reinstalls only absent or non-current ones through the existing APIs,
and probes the experimental Windows Sandbox on the actual registered workspace.
It reports hashes and expiry without configuration or credentials. The current
allowlist remains the existing service allowlist.

Rollback requires root to close server intake again and write a fresh closure
receipt, then prove the connected agent is between completed iterations:

```powershell
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs status
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs rollback --operator-approved
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs status
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs rollback_refresh --operator-approved
node .coding-tools/reports/unified-setup-20261011/rollout-r7/activate-r7.cjs rollback_agent --operator-approved
```

Rollback uses current r7 receipt identities and restores the preserved r5
package through the same supported stop/census/launch path. It does not restore
or overwrite the shared profile, policies, project, ledger, or Ubuntu release.
The external poller has the existing bounded 200-iteration lifetime at 15-second
intervals; this helper is rollout evidence, not a persistent installation.

All public phase evidence appends to `windows-activation.jsonl`. Final readiness
proof requires READY/admission-open, fully ready, matching native epoch, exact
live host/UI/native/agent identities, a fresh successful agent heartbeat, ledger
integrity and no live work. It is API/Sandbox evidence; real ChatGPT interaction
and renderer continuation remain separate acceptance checks.
