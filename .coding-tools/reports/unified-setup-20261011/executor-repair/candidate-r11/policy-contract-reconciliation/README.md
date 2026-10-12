# r11 contract-only existing-policy reconciliation

Root owns execution. Child prepared this helper and observed only read-only local
state. No product source, live policy, service, VM, action or acceptance changed.

Cause: metadata pins current service facade `3664b707…`; standing read, patch and
exec policies still pin `274af168…`. The rejected canary reached no patch/proof.

Supported packaged node-agent `install-file-read-policy`,
`install-approved-patch-policy` and `install-exec-policy` expose atomic `--replace`
for already installed policies. Unlike the enrollment UI's new-exec enablement
path, these CLI operations do not launch Sandbox. This packet only refreshes
three enabled policies for the same registered workspace. All fields besides
`facade_contract` must compare identically; metadata bytes stay unchanged.
Real execution retains the runtime Sandbox gate. No gate or policy source changes.

## Root procedure

1. Ensure rejected central task is closed and nothing is dispatching. Obtain one
   fresh public `authority-renewal-next` observe wrapper with `scoped_pilot`, the
   approved original next context/pilot window, and five target quiescence counts
   zero. This receipt must be under 60 seconds old throughout the operation.
   Do not enter recovery solely for this step; recovery revokes the active pilot.
2. Verify helper manifest. Run the following once, substituting the exact new
   observation path/hash. Keep all other task dispatch inactive while it runs.

```powershell
node .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r11/policy-contract-reconciliation/reconcile.cjs sync --operator-approved-same-scope-r11 --server=ABSOLUTE_OBSERVE_WRAPPER_JSON --server-sha256=EXACT_SHA256
```

3. Require `contract_reconciliation_complete`. It records each installed policy,
   exact noncontract equality, unchanged metadata, canonical no active work,
   no VM before/after, exact ready native identity, and old pending rows unchanged.
   Allow one connected-agent heartbeat, collect fresh server/native evidence,
   then root may prepare one new canary. Do not reuse the rejected action.

The helper pins r11 source/package parity, service facade, exact host/native epoch,
approved renewal receipt and expiry `1791739329910`. It cannot reanchor authority.
`sync-attempt.json` is exclusive and prevents silent automatic retry. A partial
failure reports only safe error codes and permits no further dispatch until root
reconciles actual policy state. Do not delete the attempt receipt or hide history.

## Evidence

Nine offline pure-fixture guard checks passed. Query-only local observation at
23:46:01 (+07) confirmed old hashes, exact host/native provenance, zero canonical
active work and zero VM/backend, with historical pending RUN/WAVE unchanged.
The child did not run `sync`. No SSH, deployment, restart, commit or push occurred.
