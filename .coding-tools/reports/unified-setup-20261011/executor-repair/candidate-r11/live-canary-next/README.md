# r11 canary for renewed authority

Local derivative of the frozen `../live-canary` bundle. Root alone executes remote phases. Product source, deployed service, package, native contract, patch, checker and proof plan are unchanged.

## Exact renewal

- Approval: `call_flEpmLChKJPZsbnlAAXR5byS`.
- Requested: `1791735729910`; expires: `1791739329910` (exact 60 minutes).
- Context: `ctx_71ae5c01e2de4df6874d401263a310c0`.
- Pilot: `pilot_b294f82a6cf64b098268322b9106d8c7`.
- New authority marker: `/home/svhome/.local/state/codex-control-plane/owner-operations/r11-initial-verification-next-60m/authority-renewal-public.json`.
- The marker must have phase `intake_reopened`, exact target/source/approval/window and matching service identity. Native epoch/process/server are proved by fresh pins and the existing live authority guard; the renewal marker does not contain those fields.

All canary intent and result files use the new operation directory. Frozen `r11_common.py` is loaded unchanged and keeps its old directory. The old authority marker must have phase `authority_renewed` and unchanged byte hash matching the new renewal marker. It is checked on input and after both successful and failed trials.

## Root procedure

1. Capture fresh native preflight, with zero active Jobs/VM work, exact source/preimage/checker and preserved old RUN/WAVE hashes.
2. Populate a new actual pins file from `pins.template.json`. Template placeholders are not runtime evidence. Use fresh deployed service/epoch/process/server identities; bind the native preflight receipt hash.
3. Run `root-canary-ssh.py prepare --pins ABSOLUTE_PINS --native-preflight ABSOLUTE_RECEIPT --expected-native-preflight-sha256 HASH`. Preparation is local only. It consumes this folder's frozen manifest, frozen common and original SSH staging helper by exact hashes.
4. Use the returned staging manifest for `stage`, then `preflight`, then exactly one `dispatch`, each with `--manifest ABSOLUTE_MANIFEST --execute`.
5. Use `observe` on the same manifest/action. Transport uncertainty forbids a second stage/dispatch/cleanup effect; reconcile existing state.
6. Correlate the returned RUN/WAVE/Job/ProofLedger using the existing `../native-live-correlation/correlate_r11.py`. Capture retained native output using the original `../live-canary/native-output-read.cjs`. Read-only observe/correlation does not replay execution.
7. Cleanup only after the same action is settled, using the same manifest. Native semantic acceptance remains pending; this packet neither grants acceptance nor supplies a new controller transport.

Fresh native preflight must be less than 60 seconds old at prepare/stage/dispatch, with at least 120 seconds remaining on authority. Do not relax these checks when stale; collect new read-only evidence before any effect.

## Local proof

35 focused offline tests passed: 16 inherited canary, 6 inherited transport, 13 derivative authority guards. SSH/subprocess/API effects are mocked; no live dispatch occurred in this lane. Independent bounded read-only review found no concrete defect. Original frozen canary, transport and common hashes remain unchanged.

`helper-manifest.json` binds local helper/test/document bytes. `proof-receipt.json` records derivative provenance, passed checks, unchanged frozen hashes and local-only scope. No commit, push, tag, release, deployment, service or authority operation occurred in this lane.
