# Source fingerprint repair — r13

The r12 production canary failed before file mutation or RUN creation with
`WORKTREE_STATUS_TOO_LARGE`. Its native performance row records the exact
approved-patch actor and validation error. Full Git status included more than
3,400 retained `.coding-tools` evidence entries and crossed the existing
2,000-entry source identity bound before evidence was filtered.

## Focused repair and proof

Only the internal source identity status query now excludes `.coding-tools`
with rooted Git pathspecs before parsing the bounded status output. Public full
Git status retains its existing behavior and bound. No evidence was deleted,
ignored, unstaged or omitted. Genuine source changes still invalidate proof;
source status overflow still fails closed. Staged renames across the evidence
boundary retain the corresponding source addition/deletion.

Changed product files:

- `resources/coding-tools-mcp/coding_tools_mcp/git_tools.py`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/tests/test_source_worktree_identity.py`

[Focused source proof](source-proof.json): four new regressions and four
existing identity/parser gates passed. A read-only harness on the actual
repository observed 3,520 full status entries, 3,412 evidence entries and
108 valid source entries. It did not construct a Runtime or create a RUN/Job.

Candidate `source-fingerprint-1012-r13` is built at
`dist/windows-candidate-mxc-wsb-cbe1774-source-fingerprint-1012-r13/win-unpacked`.
[Frozen source](source-freeze.json) and
[package parity](candidate-parity-20261011T200058268Z.json) prove 17/17 relevant
payloads match, including the two repaired Python files. The Electron archive
remains `2bd2bed8…`; the repair is in the packaged Python resources. The isolated
packaged Recovery smoke passed and preserved the production descriptor.

## Current limit

r13 has not been activated. r12 remains the live runtime. The original unknown
canary receipt and wrapper intent/result remain evidence. Exact pre-effect
reconciliation completed at 03:09:12 +07 using the genuine node receipt API;
the action is settled/rejected and its task/writer closed/released. The original
unknown receipt and unrelated history are preserved, with no patch replay or
historical acceptance. See [terminal reconciliation](../candidate-r12/reconciliation/terminal-reconciliation-receipt-20261011T200912606456Z.json).
A separate explicit r13 activation is
required by AGENTS.md section 5; current permission named r12.

The existing trial expires at 12-10-2026 03:42:15.200 +07. A new check requires
at least 12 minutes remaining immediately before dispatch. This repair does
not extend or reanchor that authority. The deployed recovery-mode operation
revokes pilots, so the intake transition must account for explicit pilot
rotation before activation; the unchanged-pilot preparation cannot be executed.
The corrected [intake packet](intake-transition/README.md) pauses once and creates
one replacement pilot with the same context/expiry, then reopens only for the
proved r13 identity. The corrected [Windows packet](activation-windows/README.md)
requires that new rotation receipt and keeps all four installed policy hashes.
Nine Windows guard tests and three intake tests pass. A live read-only server
observation at 03:16:25 confirms r12 ready, policy enabled, zero open tasks and
writers, and zero unsettled actions for this target. No r13 effect has occurred.
Ubuntu remains revision `9cae1044…`,
without deployment/restart. Git remains dirty `main @ 2c554f59`, with unrelated
work preserved. No commit, push, tag, public release or Windows reboot occurred.
