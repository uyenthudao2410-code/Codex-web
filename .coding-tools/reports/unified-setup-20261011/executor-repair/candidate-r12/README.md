# Policy contract recurrence repair — r12 local candidate

The requested workflow remains edit code → run tests → collect source-bound proof.
This candidate fixes a concrete blocker: unified setup reused standing policies
whose installed facade contract differed from fresh authenticated server authority.

## Proven local state

- Dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`; unrelated changes preserved.
- Candidate `policy-contract-1012-r12`, under
  `dist/windows-candidate-mxc-wsb-cbe1774-policy-contract-1012-r12/win-unpacked`.
- `app.asar` SHA256 `2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1`.
- [Source proof](../policy-contract-recurrence-20261012/source-proof.json):
  33 JavaScript tests, three Python inspect tests, syntax and scoped whitespace checks passed.
- [Exact candidate parity](candidate-parity-20261011T172955204Z.json):
  all 15 relevant payloads match the frozen source; no source drift.
- [Isolated packaged smoke](packaged-smoke-receipt.json): Recovery Host and MCP
  healthy, exact packaged resources/adapter, eight smart-v3 tools, fail-closed
  supervisor checks, test-owned process cleanup, production descriptor unchanged.
- Read-only independent review found an exec reuse admission gap; the worker
  fixed it before final source proof. Final scoped review found no remaining concrete defects.

Installed policy inspection now includes the validated facade triple. Enrollment
adds fresh current authority for the exact workspace/generation. UI reuse requires
matching triples and an observation less than 60 seconds old. Missing authority,
wrong target, disabled standing writes or non-admitted exec cannot be reused.
After a long Sandbox probe, setup refreshes file authority before completing.
Existing permission scope, installers, allowlists, limits and Sandbox gates remain.
No new public MCP schema, policy schema or heartbeat behavior is introduced.

## Current operational blocker

At 00:29 +07 the r11 Host PID20400 and native MCP were live, but epoch
`activation-mv438ehi-cebe9d7cb6af824eb7153869dc4435bb` remained
`UPDATE_INCOMPLETE`, admission closed, with all readiness flags false.
No connected-agent bootstrap occurred. The previous live trial expired at
00:22:09.910 +07 and cannot authorize new dispatch or runtime/authority mutations.

The [00:38 read-only observation](current-observation-1791740326987.json)
confirmed the same live Host/native and absent connected agent. Canonical census
reported zero active tool calls, commands, starting commands, background work,
managed processes or agent lanes. `RUNTIME_BUSY` referred only to the live runtime
process; historical stale classifications were preserved. Ledger integrity was
`ok`, pending RUN/WAVE hashes and canary target preimage remained unchanged.
The helper's first attempt failed on its local path handling before emitting an
observation; that helper error was corrected, without runtime/authority effects.

At 00:47 +07 the new guarded Windows transition helper's **observe-only** phase
passed exact package/source/dependency checks, authenticated Host IPC,
registration/config checks, canonical census and pending-record checks. It also
proved independent VM/backend counts were zero. Host, UI and native remained
live; the agent remained absent and epoch/admission/readiness stayed incomplete.
The [append-only observation](activation-windows/attempts/r12-readonly-20261012-0047/transition.jsonl)
has no runtime or server effects. A read-only SSH `true` command also exited zero.

No r12 production activation, Ubuntu deployment/restart, trial renewal, canary
patch/test Job, semantic acceptance, commit, push, tag, release or Windows reboot
has occurred in this wave. Historical pending acceptance is preserved.

Next: prepare the guarded activation packet, request one explicit r12 activation
and exact-scope 60-minute renewal, then bootstrap the bounded registered agent
before final READY verification. A new canary requires at least 10 minutes plus
margin remaining in the trial. Live edit/test/proof and genuine native ChatWeb
acceptance are not proven by the local package tests.

## Final preparation checkpoint — awaiting r12 approval

All three local packets are complete:

- [Windows transition](activation-windows/README.md): 10 narrow guard checks,
  syntax and dependency parity passed. Final helper SHA256
  `71972c3aa7f88cb625d44507ef5e3b69ca6921a21d6f2520bde0fff5119f5927`,
  manifest `20a507338148c9d108e7ad0f75f2a8e3ac04940ca216f329c83147563c99f679`.
  Final independent review verified exact server/renewal scope and window,
  no replay, bounded bootstrap, one refresh and sanitized recovery child lineage.
  A final wrapper correction normalizes native Windows PowerShell modules only
  in the helper process, including its process-identity broker. Syntax passed;
  unchanged authority tests are reused and prior reviewed bytes remain evidence.
- [Authority renewal](authority-renewal/README.md): 15 offline checks passed.
  The existing Ubuntu release is retained; actual new approval and fresh server
  observations are required before staging or any authority effect.
- [Canary and correlation](live-canary/README.md): 30 Python and three Node
  offline checks passed, with syntax/whitespace checks. A genuine new reopened
  receipt and fresh native identity are required before dispatch.

One operator question now requests r12 activation on the exact profile and a
60-minute same-root read/edit/exec renewal on the existing Ubuntu destination,
including scoped intake and local policy sync followed by one canary. No answer
has been recorded in this checkpoint; no dependent effect has been performed.
The reason is AGENTS.md section 5 and the expired r11-specific trial, not a new
scope expansion. The next action after approval is fresh read-only pinning,
controlled renewal and the guarded transition. Fresh observations must replace
the older 00:47 evidence before effects.

Final local Git observation showed 82 modified and 3387 untracked entries,
zero conflicts, preserving the prior work. No commit or push is requested or
performed. New report artifacts remain repository evidence for eventual delivery.
