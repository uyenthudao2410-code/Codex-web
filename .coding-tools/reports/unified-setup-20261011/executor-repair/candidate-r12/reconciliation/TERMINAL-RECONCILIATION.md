# One genuine pre-effect rejection, then exact task close

Root may execute this only with the actual fresh native no-effect proof. This
packet is bound to approval `call_1KzUkF0gMn6uVpHd3QisTzXF`, existing r12 scope
and expiry; it grants no capability and changes no package, service or runtime.

Exact target: `Tools-Codex-web` on `DaoChienThang`, profile `web-mcp-assistant`,
binding `bind_3e05bf64cb3e4bab93d930ae1692bebb`.

Exact dispatched family:

- Action `act_6aa1329b96c146f38c807f9926b3e684`.
- Task `task_d2c1dd3bff4042d084b045e9bc5a381b`.
- Attempt `try_4178cd41d2f3424a81dcb3c4cc706ed1`.
- Original unknown receipt `rcpt_9117fdebb06b4e8e8b1b5cd1b65ed2b1`, payload
  SHA256 `09b5eeb50c371e333d23da019ec4d443d8e22d9aaaf2914472c802cbbacb38c2`.

## Why task close must follow reconciliation

Current source `Store._release_task_writer_lease_in_transaction` refuses a
dispatched, accepted or `reconcile_required` action. Both task-close paths call
it. Closing a task first cannot safely release the held writer. The historical
read-only quarantine endpoint is scoped to `workspace_context`; it is not a
patch reconciliation route.

The existing node-authenticated route
`POST /v1/nodes/<exact device>/receipts` accepts a terminal `rejected` receipt for
the already-delivered exact attempt. With a genuine pre-effect observation, it
appends a truthful receipt and settles the action while retaining the original
unknown receipt. Only then does supported `workspace_context.task_close` release
the exact task's writer lease and close its intake. No local node journal is
modified and no action is dispatched again.

## Root command

```text
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r12/reconciliation/root-settle-ssh.py
  --execute --operator-approved --approval-id call_1KzUkF0gMn6uVpHd3QisTzXF
  --query ABSOLUTE_QUERY_RECEIPT --query-sha256 ACTUAL_FILE_SHA256
  --native ABSOLUTE_FRESH_FINAL_NATIVE_PROOF --native-sha256 ACTUAL_FILE_SHA256
  --authority ABSOLUTE_ORIGINAL_R12_REOPEN_RECEIPT --authority-sha256 ACTUAL_FILE_SHA256
```

Use only the final native receipt from `root-native-no-effect-census.cjs`, not its
preliminary evidence. Required observation younger than 60 seconds: unique actual
`WORKTREE_STATUS_TOO_LARGE`/`validation` before RUN/Job/proof, unchanged target and
checker, preserved prior pending records, current native identity, canonical
quiescence and the bounded Sandbox/backend process census. Its process census
does not claim physical HCS inventory; use the explicit evidence basis recorded
by the native observer.

Driver loads only the existing exact-profile DPAPI-protected node config. It
uses the pinned packaged `_unprotect_node_secret` decoder in memory and never
invokes `_config`, avoiding migration writes. Credentials travel only in memory
over encrypted SSH stdin, and are excluded from files and all public output.
Operator/tunnel credentials on Ubuntu remain memory-only through existing
protected helpers. No staging or deploy/restart operation exists.

The remote helper rechecks exact release, service instance, authority marker,
approval/window, one attempt/task link and original unknown payload. Local and
remote exclusive intents prohibit automatic retries. Its postconditions require
the original unknown receipt unchanged, one new rejected receipt, exact action
settled, exact task closed/writer released and unrelated protected rows unchanged.
Partial or unknown outcomes require read-only observation of that exact family;
never delete an intent or write a fabricated completion receipt.

Before task close, a read-only database snapshot verifies the new receipt's
action, device, empty handle, exact payload and digest. The digest binds the
original attempt even when the HTTP response does not echo `attempt_id`.
The complete delivery-attempt row remains fingerprinted unchanged; the receipt
timestamp must match the settled action timestamp. The final snapshot repeats
these guards after closing the exact task.

## Local proof and state

Both helpers compile. Eight focused offline tests pass, including a successful
response without an echoed attempt, a deployed response with its echo, rejection
of replay, wrong attempt digest, device/action/handle/timestamp or payload drift,
and preservation of the old receipt, action arguments and lease generation.
Earlier synthetic checks cover exclusive intent no replay. The Linux `O_NOFOLLOW`
constant is mocked only for a temporary Windows test fixture. The lane performed
no SSH/API/runtime/authority effect, commit, push, deploy or service restart.
Git remains dirty `main @ 2c554f59…`; all previous source and evidence remain.
