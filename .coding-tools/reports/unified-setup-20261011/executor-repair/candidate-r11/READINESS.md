# r11 initial structured proof — preparation checkpoint

Repository: `E:\Github\Tools-Codex-web`, dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`.
Prepared on 2026-10-11. This is source/local-package evidence; r11 has not been activated or deployed.

## Completed behavior

- Exact optional verification argv/cwd/limits are immutable across permission, intent, action and idempotency. Both patch and execution policies must admit the same registered root before writing.
- Native expiry is checked under the file patch lock before commit and again after Sandbox preparation before process launch. Exact patch bytes, including a trailing newline, retain their binding.
- One initial structured check uses the existing source-bound ProofLedger and the patch's own RUN/WAVE. Failed/timed-out proof retains its completed patch effect and REPLAN. Duplicate requests and slow-operation observation do not replay either patch or check.
- Legacy no-plan requests retain their previous identity. Genuine controller acceptance remains separate; this controller has no exposed authenticated native ChatWeb acceptance transport.

Changed boundaries: Electron approved-patch bridge/Recovery Host/runtime orchestrator; native workflow/context/file/exec/schema plus its leaf helper and module extraction; Control Plane facade/Store/node/recovery serializer; corresponding tests and current-state documents. Unrelated dirty work and historical evidence remain intact.

## Validation actually performed

| Check | Evidence |
| --- | --- |
| JS approved-patch bridge | 10/10 passed |
| JS runtime request/schema/operation observation | 6/6 passed |
| Recovery Host actual policy/target wiring | 4/4 passed, including subtests |
| Native initial-proof behavior | 10/10 passed; existing idempotency/source-cache focused cases also passed |
| Native extraction/full suite | Original run: 1218 passed, 5 failed, 5 skipped; not a green full suite |
| Two full-suite fixture fixes | Exact contract SHA assertion and same-command bounded polling each passed a focused retry |
| Remaining three full-suite cases | Real Sandbox continuation fixtures refused `SANDBOX_HOST_BUSY` before provisioning/spawn; live gate remains open |
| Isolated boundary diagnostic | 4/4 passed; five synthetic spawns all shell=False, one failed-proof repair, one same-command poll; no real process/VM |
| CP permission/intent/migration/node/facade | 31 distinct Python cases passed |
| CP recovery serializer | 3/3 CJS passed |
| CP release format | 38 payload files verified, schema29 |
| Offline schema29 closed recovery | 7/7 invariants passed, history/new columns preserved, intake/dispatch/new authority/acceptance denied |
| Windows candidate | Build passed; 12 affected payloads match frozen source; no source drift |
| Isolated packaged smoke | Passed: exact resources/adapter, smart-v3 eight tools, Recovery ready, supervision/fail-closed checks, own-process cleanup, production descriptor unchanged |
| Git/static | Scoped syntax and whitespace checks passed; no Git conflicts |

Bundled Python lacks pytest; the required full suite used the explicit previously verified Python311 interpreter without installing dependencies. Original failures and diagnostic attempts remain in the evidence tree; focused retries do not rewrite the original suite result.

## Immutable package identities

Windows: `dist/windows-candidate-mxc-wsb-cbe1774-initial-proof-1011-r11/win-unpacked`.
`app.asar` SHA256: `2071c0c242bc4b24ebfc22ea21b5c4d066e018505061ebe299cd666c6d2e8a91`.
See [parity receipt](candidate-parity-20261011T142316263Z.json) and [isolated smoke receipt](packaged-smoke-receipt.json).
Native public smart-v3 tools/list SHA: `0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4`; current discovery/contract refresh must confirm it after activation.

Ubuntu main artifact content revision: `9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c`.
Archive SHA256: `7d1a0b015208b4fc257a52bc888cd8a15f559ce33cf04846953d533002b7c273`.
Exactly four runtime payloads differ from Store395; 34 retain their bytes. [Packet and migration notes](../initial-proof-server/README.md).

Emergency recovery content revision: `81303f7cf4d006c5e6e2eeaffb578b57446b9dbd6730c9f34b2a7bec98b8c0cb`.
It supports only an existing schema29 database with persisted closed recovery admission and preserves subsequent history. [Recovery proof](../initial-proof-server/rollback-preparation/proof-receipt.json).
Never lower schema version or restore the old database over later task history. Main and recovery content revisions are artifact identities, not Git commits.

## Current state and next action

The r10 trial expired at 20:48:18.491 +07. Its recovered runtime was last verified READY at20:38; Store395 is the last deployed server identity. This wave made no production activation, SSH/deployment, service restart, authority renewal, commit, push, release or Windows reboot. Isolated smoke processes exited.

Query-only local observation found SQLite integrity `ok`, no managed Job records classified as active, no unexplained live resource or projection drift; the original pending RUN/WAVE hashes remain exact. Seventeen historical stale candidates and the pending acceptance record remain preserved. [Observation](final-local-observation-1791728141717.json).

Next: after destination-specific authorization under AGENTS §5, preflight exact current identities/jobs, close intake, preserve a consistent server backup, deploy the pinned schema29 main package, restart the Ubuntu user service, activate the pinned Windows candidate through supported lifecycle, refresh contract, and open only the approved folder/time scope. Use the closed recovery package only for a verified failure requiring controlled recovery. Run [one NEW patch acceptance canary](NEW-PATCH-ACCEPTANCE.md), observe the original operation/Job/source proof and record the remaining authenticated controller acceptance gate. Do not replay old patches or accept/reject the old pending RUN/WAVE.

Durable installed-agent lifecycle, controlled cleanup/timeout evidence and signed installer remain separate unproven product gates. Source/package preparation is complete; live end-to-end completion is not claimed.
