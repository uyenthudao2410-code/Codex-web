# Adopt the exact r11 child and recover native MCP

Root's first launch created PID `2088`, start token `134362091929075790`, Recovery instance `5dbfd12d3570204cb1a89058f910ccec`. Two independent read-only probes verified the exact descriptor and authenticated IPC. Job association is true; which Job and its lifetime are unproven. The helper preserves that warning and never labels the process independent of every Job.

At 23:21–23:22 +07, the persisted central READY proof was adopted and UI was healthy, registered, PID `25148`. Native old PID `24044` was absent, `manualStop=false`, `failureKind=mcp_process_exited`, `recoveryBlocked=true`; the read model therefore closed admission. `ready_adoption` was `adopted`, so this is not a malformed READY role-proof. The supported recovery is one exact `full_clean_refresh`, preserving the pending acceptance hashes.

Use **`adopt-exact-child.cjs`** with its own `adoption.jsonl`, preserving frozen original helpers and failed attempt evidence. Mutation phases require the fresh closed server receipt and this helper's exact SHA as before. Add `--acknowledge-job-associated-lifetime-risk` for adoption and agent launch. Agent creation may return a PID plus association warning; the helper records/adopts that same exact child after querying its identity, with no repeat. Successful heartbeat remains a separate live gate.

Root sequence:

1. `adopt` with fresh server receipt and explicit lifetime-risk acknowledgement.
2. `policy` with the newly approved renewal receipt.
3. `agent` with that exact renewal and lifetime-risk acknowledgement.
4. `refresh` with fresh server receipt plus exact renewal; this invokes supported Recovery IPC once with `allowAcceptancePending=true`.
5. `status`; a replacement descriptor is accepted only through the durable exact-host handoff proof from that refresh.

Renewal is **23:22:09.910 → 00:22:09.910 +07**; context `ctx_71ae5c01e2de4df6874d401263a310c0`, pilot `pilot_b294f82a6cf64b098268322b9106d8c7`. These are server authority facts reported by root, not authority created by this preparation.

No additional runtime was launched, killed, retried, or refreshed by this lane. Source/package, old RUN/WAVE, and Git dirty `main @ 2c554f59` are preserved. Root performs live actions and final acceptance.
