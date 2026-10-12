# Exact r10 full-clean handoff continuation

Observed 2026-10-11, dirty `main @ 2c554f59`. Root owns execution. This packet adds no source, runtime or authority change by preparation.

The frozen v2 refresh returned HANDOFF for `activation-mv3tn5og-8def0602e3d318e0c42052c6eefc00ba`, operation `full-clean-mv3tmvoi-424499179795d11e85d23af6`. Full-clean intentionally retired host 24760/`96b17ff815a3028b43929ddf0e3b212e` and assembled host 14516/`683d283f8174b82d1c906d53fd41e190`, UI 15660, native 6064. The original `currentR10` pins the pre-refresh host and correctly refused this changed identity. This additive helper recognizes only the documented durable handoff with the exact replacement OS start tokens, epoch, operation, transition chain, current native epoch, component revisions and census.

## Frozen inputs and output

- `activate-r10-v2.cjs`: `4b689f8533f1de77130257543b408aec43b3f91e79579015a7a10a054db06b05`.
- `windows-activation-v2.jsonl`: `4213950067cc15136df9dfd4da95978c5d216f47754ac37464367da7ab2a24b3`. Do not append; continuation refuses drift.
- `continue-r10-handoff.cjs`: `9287d28b1d472ea790ea305c683b2b249103db9d87a87f9ee5c7a13608f983fa`.
- New output only: `windows-handoff-continuation.jsonl` and the existing bounded-agent stdout/stderr files from v2.

The loader checks immutable v2 bytes and removes its exact terminal CLI invocation in memory. It reuses original package/source, operator authorization, server receipt freshness, standing policy and pending-acceptance guards under the original filename. Three explicit hooks redirect emit, combine read-only receipt lookup, and require the exact post-handoff host. Frozen files are never rewritten.

## Root CLI

Use the same reviewed authorization/server hashes and exact local-proof basenames that succeeded for v2. All four explicit SHA flags remain mandatory for `agent`:

```text
node continue-r10-handoff.cjs agent --operator-approved --authorization-sha256=<exact> --server-preflight-sha256=<exact> --closure-sha256=<exact> --renewal-sha256=<exact> --closure-local-proof-file=<exact> --renewal-local-proof-file=<exact>
```

`prepare` is read-only runtime observation plus repository evidence. `agent` repeats preparation and original mutationGuard, verifies zero VM/backend processes immediately before the spawn, then invokes the unchanged bounded-agent path. It is admitted while the exact durable epoch is VERIFYING/CLOSED and unexpired, because an authenticated heartbeat is needed to establish a fresh central route. It never marks readiness; the supported host final census must establish real READY. `proof` requires that READY, actual fresh heartbeat, same target policies, no active jobs/lanes and unchanged pending RUN/WAVE records.

No activation replay, refresh, restart, metadata install, intake/authority mutation, acceptance, test execution, process termination or readiness fabrication is exposed. The existing 20:00:37 epoch TTL and original server receipt freshness checks are preserved. If a guard rejects, report its precise code; do not rewrite timestamps or widen identity pins.

## Validation and state

`node --check continue-r10-handoff.cjs` passed. Source analysis read only the exact current epoch, runtime PID/token/epoch fields and frozen v2 journal. No live IPC/heartbeat/service/action mutation was performed by this lane. Root must execute and report runtime proof separately.
