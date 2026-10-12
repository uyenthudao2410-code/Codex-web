# Exact r12 action diagnosis — read-only

Root executes:

```text
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r12/reconciliation/root-query-ssh.py
```

The pinned query is streamed as binary stdin and compiled in server memory.
No stage, remote file, service/release operation, authority change, action replay
or cleanup is performed. The frozen r11 SSH public-receipt parser is reused.
Operator credentials are read by the existing protected environment helper and
used only in memory for GET `/healthz`. Raw stderr and receipt payloads are never
printed or stored.

Only existing action `act_6aa1329b96c146f38c807f9926b3e684`, task
`task_d2c1dd3bff4042d084b045e9bc5a381b`, their target and one delivery attempt are
queried through SQLite `mode=ro`, `query_only`, a snapshot transaction and an
explicit close. The dispatch response is verified from the existing private
r12 canary directory. The query does not invoke the canary's mutation functions.

Public output includes action state, exact attempt/receipt IDs, receipt codes
and `diagnostic_code`, boolean patch claims and existing reconciliation or
dispatch disposition. An unknown receipt remains unknown until exact native
journal/file/proof observations are correlated; this query never authorizes
cleanup or asserts that a patch was applied.

Local proof: both Python files compile; synthetic unknown receipt exposes only
allowed diagnostic fields, excludes injected private fields, binds the exact
action/task and leaves the synthetic database bytes unchanged. No SSH or live
runtime effect was performed by this lane. Root owns live observations.

Git remains dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`; this wave
added only this new directory and preserved all existing packets and work.
