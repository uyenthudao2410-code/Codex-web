# r13 canary bound to the newly approved 5-hour window

Root owns live effects under approval `call_a60e931056bd402b997c6c10b0796d81`.
This new subtree preserves r12 and the unexecuted r13 same-window packet. It
adapts the tested r12 trial: same fixture, checker, patch, 60-second verification
plan and one-dispatch semantics. New keys start `r13_5h-initial-`; remote evidence
is separate under `r13-initial-verification-5h/canary`.

Native query-only preflight pins r13 package `source-fingerprint-1012-r13`, its
17 exact source payloads, and source-freeze `e9351a36…`. The new common helper is
SHA `25f2d153…`, changing only renewed-authority duration validation to 5 hours.
Old r12 marker remains immutable SHA `a3c5c2ee…`.

## Actual authority and root sequence

Use the real `r13_5h_intake_reopened` receipt after Windows r13 is READY, never the
expired r12 or unexecuted same-window receipt. The actual renewal starts once at
`1791758571067`, expires `1791776571067`, context
`ctx_1e7e2fec6f0e43018db7a51c6980e5c2`, pilot
`pilot_b1cb26c319fb489aae24d3b746318447`. These are observed values, not templates.
Reopened marker digest and runtime identities still require actual fresh proof.

Resolve Node and Python each to one exact executable path. Let `C` be this
directory. Individual helpers only; no convenience orchestration wrapper.

1. Run `node C/native-preflight.cjs` after exact scoped reopen. Save its exclusive
   query-only public receipt; no checker, Job, service or VM is started.
2. Freeze new pins with `pins.template.json`: copy scope/service/window/approval
   from actual reopened receipt, native identity/preflight from fresh receipt,
   exact authority/native receipt hashes and new marker hash. Preserve old hashes.
3. Within 60 seconds and with at least 12 minutes remaining:

```text
python -B C/root-canary-ssh.py prepare --pins ABSOLUTE_PINS
  --native-preflight ABSOLUTE_NATIVE --expected-native-preflight-sha256 ACTUAL_SHA
  --authority-receipt ABSOLUTE_5H_REOPEN --expected-authority-receipt-sha256 ACTUAL_SHA
python -B C/root-canary-ssh.py stage --manifest ABSOLUTE_RETURNED_MANIFEST --execute
python -B C/root-canary-ssh.py preflight --manifest ABSOLUTE_RETURNED_MANIFEST --execute
python -B C/root-canary-ssh.py dispatch --manifest ABSOLUTE_RETURNED_MANIFEST --execute
python -B C/root-canary-ssh.py observe --manifest ABSOLUTE_RETURNED_MANIFEST --execute
```

Dispatch exactly once. Repeat only read-only observe. An ambiguous outcome
requires reconciliation; never delete a consumed intent or automatically retry.
Stage uses a fresh `r11-approved-UTC` incoming directory required by the frozen
transport; all six files are new, and no older trial directory is reused.

After durable completion, root uses adapted `native-output-read.cjs` and
`correlate_r13_5h_source_identity.py` for authenticated retained output and exact
ledger lineage. This derivative matches the native r13 Git pathspec exclusion
before the source-entry bound; the original correlator and manifest are retained.
Capture complete bounded TAP 4 pass/0 fail and empty stderr within 300 seconds;
exit zero alone is insufficient. The Electron reader uses the authorized
`web-mcp-assistant` crypto profile with `ELECTRON_RUN_AS_NODE` cleared, and creates
no BrowserWindow or production mutex. Use the preserved r12 reader procedure
with this new script path and one executable path.

```text
python -B C/correlate_r13_5h_source_identity.py --receipt ABSOLUTE_OBSERVE
  --pins ABSOLUTE_PINS --output-receipt ABSOLUTE_NATIVE_OUTPUT
python -B C/root-canary-ssh.py cleanup --manifest ABSOLUTE_RETURNED_MANIFEST --execute
```

Only the exact settled new task/writer may close. Native semantic acceptance
remains a genuine controller operation. Helpers never accept old RUN/WAVE,
fabricate attestation or change a Console verdict.

## Validation and state

19 focused canary tests and four offline bundle tests pass: dynamic 5-hour
receipt/marker binding, old marker preservation, wrong identity/scope/window
refusal, exclusive no replay, own-context causal filtering and no database
mutation. Python AST, Node syntax and actual r13 17-file package parity pass.
Two derivative source-observation tests pass: retained evidence is excluded
before the bound, ordinary dirty source (including current docs) remains bound,
and excessive source entries still reject. The actual read-only repository
observation passed with 108 source entries while the all-status census contained
over 3,600 evidence/source records. Job/proof/old-pending correlation is unchanged.

This lane performed no live SSH/API/IPC, dispatch, activation, deploy, service
restart, reboot, commit or push. Root separately completed 5-hour authority;
live canary and semantic acceptance remain unproven here. Git stays dirty
`main @ 2c554f59…`.
