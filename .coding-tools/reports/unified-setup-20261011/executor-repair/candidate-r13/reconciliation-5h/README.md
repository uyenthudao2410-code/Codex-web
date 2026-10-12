# Exact r13 five-hour action diagnosis — read-only

Root executes:

```text
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r13/reconciliation-5h/root-query-ssh.py
```

The new observer derives from the retained r12 observer and streams a hash-pinned
query through binary stdin for compilation in server memory. It creates no
remote file and performs no service, release, authority, replay or cleanup
operation. The existing frozen r11 public-receipt parser is reused. Operator
credentials stay in memory for GET `/healthz`; raw stderr and receipt payloads
are never printed or saved.

The query pins action `act_b2335c57472b4d68931d10dda1572ff9`, task
`task_3b2a2a860ca54ef7889d2efce6923dc7`, the target, principal, one delivery
attempt, schema 29, existing r13 dispatch marker, and the five-hour common hash.
SQLite opens in `mode=ro`, sets `query_only`, begins one snapshot transaction,
and closes explicitly. It reads only the exact family.

Public output allows receipt codes, diagnostic codes, boolean patch claims,
bounded proof/run/wave/command/Job IDs, native identity, file hashes and existing
reconciliation/disposition. Raw file paths are replaced by a boolean canary-path
match. Missing patch claims remain unknown. Central claims still require exact
native journal, file, Job and proof correlation. The query grants no cleanup,
reconciliation, acceptance or replay authority.

Prepared by the review lane; root alone owns SSH and live observations. The
native diagnostic output reader in this directory belongs to the parent lane.
No source/package or existing frozen packet was edited. Git remains dirty
`main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`; no commit/push/release occurred.

Local validation passed: both helpers compile and match manifest pins; synthetic
SQLite uses a read-only URI, query-only snapshot and explicit close with zero
changes; database bytes remain unchanged; missing patch claims remain unknown;
diagnostic and completed-proof projections exclude injected private fields; a
wrong target is rejected with the database closed. The first test harness run
had a fixture INSERT placeholder mismatch; the corrected harness passed.
No live query was executed by this lane.
