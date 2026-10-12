# Same-expiry recovered-epoch MCP acceptance packet

Prepared 2026-10-11, dirty `main @ 2c554f59`. Root executes. This lane adds only transport/verifier helpers and this guide. Existing canary, transport, verifier, source/package, journals, ledger and runtime are preserved; no live command/IPC/SSH/authority operation was performed here.

## Transport

`root-mcp-transport-v3.py` SHA `e8143894c4633294fb492649587735bf42f2592c1474ac635a05f419659e4542` loads exact frozen original transport `a081b293…` and reuses the unchanged canary v2 `54f8ee88…`. It supports only preflight/execute. Root supplies the fresh supported replacement receipt:

```text
python -B root-mcp-transport-v3.py preflight --pins-file <reviewed-new-epoch-pins> --mode cold --reopen-receipt-file <candidate-r10/activation/server-recovery-reopened.json> --reopen-receipt-sha256 <exact receipt SHA>
python -B root-mcp-transport-v3.py execute --pins-file <same pins> --mode cold --root-execute --expected-state-sha256 <preflight SHA> --reopen-receipt-file <same receipt> --reopen-receipt-sha256 <same SHA>
```

Use warm only after the same recovered epoch/pilot has a successful cold task. Change `--mode` and use its fresh reviewed preflight. Original no-replay markers are retained; the marker key uses the actual replacement pilot.

Pins must use `pilot_id = receipt.newpilot_id`, `activation_epoch_id = receipt.activation_epoch`, and `rollout_receipt_sha256 = receipt SHA`. The guard requires the same original service/context/grant/binding/source/package/requested/expiry, original revoked pilot correlation, fresh distinct recovered epoch, unchanged authority/marker/grant/pending flags and a digest-valid receipt state. Original renewal bytes are pinned. Receipt age is bounded to ten minutes and expiry stays **20:48:18 +07**. The unchanged canary also demands ten minutes remaining, so start preflight/execute before **20:38:18**.

The supported close revoked the original pilot; this packet admits only its receipt-bound same-expiry replacement. It does not create a pilot, renew authority, reopen intake or change runtime. Frozen canary live inspection still verifies exact source/package/service grant, context/pilot and actual ready native node before dispatch.

## Generic native Job correlation

`verify-r10-native-job-v3.py` SHA `7109c9ca8ece117601a2295369884c2d37f04bfd674552844d8cc8be50e6527e` accepts explicit reviewed evidence pins:

```text
python -B verify-r10-native-job-v3.py --pins-file <same-directory pins JSON> --pins-sha256 <exact> --transport-file <completed same-directory transport JSONL> --transport-sha256 <exact> --mode cold --action-id <exact terminal action> --task-id <exact terminal task> --response-sha256 <exact> --output-sha256 <exact>
```

It verifies the complete immutable request/preflight/queue/terminal/cleanup family, exact submitted schema-1 journal action/attempt/receipt, native identity/contract/actor, response projection hash and combined output hash. One durable Job must match command/Job ids, genuine positive root PID/start token, exited lifecycle, owner/native identities, timestamps, command hash and exact RUN/WAVE equality. A later recovered epoch has different real PID/token values; they come from its matching durable Job rather than the old canary PID.

Reads use SQLite `mode=ro`, `query_only=ON`, one snapshot transaction. Output contains only bounded safe correlation metadata. No stdout/stderr, protected configuration, full journal or raw metadata is printed. Empty equal RUN/WAVE is reported as standalone exec. Matching nonempty RUN/WAVE still does not by itself prove source-bound ProofLedger or acceptance; both remain explicitly unproven.

## Validation and next action

Both helper sources passed `compile(...)` syntax validation without executing their main or writing bytecode. Root should pin the final hashes, run the fresh receipt-bound preflight/cold/warm sequence if the window remains sufficient, then invoke v3 correlation once per completed transport. No replay of the old cold action is required. Retain original artifacts and any failure evidence.
