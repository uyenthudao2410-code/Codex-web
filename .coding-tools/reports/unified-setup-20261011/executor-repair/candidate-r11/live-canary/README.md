# r11 exact patch + initial verification canary

Prepared locally for the root rollout controller. This directory does not grant
authority, activate a runtime, restart a service, or dispatch automatically.
Provenance is a **central MCP service trial**, never a genuine ChatWeb call.

## Inputs and stage

`patch-envelope.txt` is the exact immutable packet from `NEW-PATCH-ACCEPTANCE.md`,
UTF-8 with no trailing newline. The opt-in checker stays outside the patch.

Run local validation only:

```powershell
python -B .coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r11\live-canary\r11_mcp_canary.py stage
python -B .coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r11\live-canary\test_r11_mcp_canary.py
```

Root stages `r11_mcp_canary.py`, `patch-envelope.txt`, a completed `pins.json`, and
the **exact frozen** `activation-server/r11_common.py` in the same private Ubuntu
incoming directory (directory 0700; files 0600; owner `svhome`). The helper checks
common SHA `c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f`
before import. No r10 embedded guard or arbitrary dynamic module is loaded.

Pins come from the actual r11 authority renewal, reopened intake and a fresh
root-owned local read-only native verifier. Copy the exact 60 minute window,
context/pilot/service/native identities into `pins.template.json`; the template
cannot run. Native preflight must be younger than 60 seconds at dispatch, match
source/checker and both preserved pending RUN/WAVE hashes, and show no active Job.
The helper checks the receipt hash shape but cannot authenticate local evidence
from Ubuntu: root must verify that receipt against the real Windows snapshot.

## Separate explicit phases

In the staged directory, root invokes each phase separately:

```text
/usr/bin/python3 -B r11_mcp_canary.py preflight
/usr/bin/python3 -B r11_mcp_canary.py dispatch
/usr/bin/python3 -B r11_mcp_canary.py observe
/usr/bin/python3 -B r11_mcp_canary.py cleanup
```

`preflight` performs read-only r11 release/schema29, service/grant/policy/epoch,
heartbeat, context/pilot and live façade contract checks. It gets contract from
`tools/list` and requires agreement with `workspace_context inventory`. The
standing-write schema must expose the exact four-field `verification` plan.
Native `contract_version` is a separate pin, never used as façade contract.
Standing policy telemetry is a separate short freshness window: its typed expiry
must be after the observation and within 60 seconds of the last heartbeat. It is
not required to equal or cover the 60 minute context/pilot/grant window.

`dispatch` writes and fsyncs an exclusive marker under the existing private
owner-operation directory **before `task_open`**, then opens one task, claims its
writer, rechecks authority/instance/fresh native source receipt, and queues one
standing patch with initial verification. Each subsequent effect has a separate
immutable intent/response receipt. There is no retry path in the helper.

`observe` never uses the quiescent common `inspect()` gate. It observes the same
action and reads the exact task/intent/action/receipt family privately. If a
response was lost, deterministic keys recover existing IDs from the database;
it never resubmits `task_open`, writer claim or patch. Historical action-family
hashes and central acceptance rows must remain unchanged. One delivery attempt
maximum is required; a second attempt needs root review. Unknown effect blocks
cleanup and replay. Missing action also blocks cleanup; root must reconcile the
partial task separately after reading its exact state.

`cleanup` requires the action to be settled, validates any completed sealed
receipt, writes its own one-time intent, releases the writer, then closes the
task. Read-only database checks confirm task/writer terminality. Any uncertain
cleanup response must be inspected; do not repeat cleanup automatically.

## Strongest supported claim

The receipt check pins path/preimage/postimage/bytes, plan SHA, task/writer
generation, façade and native instances, new RUN/WAVE IDs, proof IDs/fingerprint
and correlated command/Job IDs when present. Failed proof never receives an
invented passed fingerprint or Job. Public output is a constructed allowlist;
raw protected config, authorization, local handle, policy and raw receipt are
never printed. Credentials remain in protected Ubuntu config/header and memory.

Passed receipt summary alone does **not** establish Sandbox Job exit 0, checker
4/4 or native ProofLedger source binding. Root's separate local read-only
correlator must prove those exact Job/command/RUN/WAVE/epoch identities. The
helper never calls native `accept` or records a central Console verdict.
Genuine native semantic acceptance remains pending with typed gap
`NATIVE_CHATWEB_ACCEPTANCE_TRANSPORT_UNAVAILABLE`.

Prepared files and offline tests are repository evidence only. Live dispatch,
cleanup, rollout and final acceptance are owned by root.

## Root binary SSH transport

`root-canary-ssh.py` reuses only `STAGE`/`INVOKE` from the fixed sibling rollout
transport after pinning its SHA
`d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba`.
It adds no credentials or embedded r10 guard. Root supplies completed public pins
and a genuine fresh local read-only native receipt. The receipt can be flat or
have the fields under `native_preflight`; every pin field except `receipt_sha256`
must agree, and that hash must equal the exact receipt file bytes.

```text
python -B root-canary-ssh.py prepare --pins <completed-pins.json> --native-preflight <fresh-native-public-receipt.json> --expected-native-preflight-sha256 <file-sha256>
python -B root-canary-ssh.py stage --manifest <returned-staging-manifest.json> --execute
python -B root-canary-ssh.py preflight --manifest <same-manifest.json> --execute
python -B root-canary-ssh.py dispatch --manifest <same-manifest.json> --execute
python -B root-canary-ssh.py observe --manifest <same-manifest.json> --execute
python -B root-canary-ssh.py cleanup --manifest <same-manifest.json> --execute
```

`prepare` is local only. It creates a new immutable binary archive/custom manifest
for exactly common, helper, envelope, pins and native preflight receipt. `stage`
sends those bytes over SSH to a new private `r11-approved-<UTCtimestamp>` directory.
Root must stage and dispatch while the native receipt is younger than 60 seconds.
The actual 60 minute authority must already be active; transport never renews it.
Native contract is pinned to
`sha256:0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4`.

Stage/dispatch/cleanup create local exclusive transport-intent markers before SSH.
Uncertain transport blocks automatic replay. `observe` retains the same staged
manifest/pins and does not create an effect intent. Public remote receipts are
stored under this directory's `remote-receipts` with fresh exclusive filenames;
stderr and raw outputs never enter repository evidence. The transport wraps the
helper result in `public_receipts`; the native correlator reads its exact helper
observation from that list.

## Capture native retained test output before 300 seconds

After the canary is settled and its sealed initial proof summary passed, root
runs the query-only correlator first to get the exact durable Job `finished_at`
as `completed_at_ms`. Launch the credential-only Electron reader before 300
seconds have elapsed since that Job finish; supply hash-pinned observation and
the same completed pins file:

```powershell
& 'E:\Github\Tools-Codex-web\node_modules\electron\dist\electron.exe' '--user-data-dir=C:\Users\daoth\AppData\Roaming\web-mcp-assistant' 'E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r11\live-canary\native-output-read.cjs' '--observation=<absolute-observe-receipt.json>' '--observation-sha256=<file-sha256>' '--pins=<absolute-completed-pins.json>' '--pins-sha256=<file-sha256>' '--completed-at-ms=<durable-Job-finish-ms>' '--receipt=E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r11\live-canary\native-output-<UTCtimestamp>.json'
```

The helper requires the actual authorized crypto profile, supported `SecretStore`
and its in-memory native MCP token. It starts no native runtime, node agent, VM,
BrowserWindow or acceptance. It uses the **public** native `command_control`
`action=read` adapter (internal `read_output`) for exact command stdout/stderr at
offset zero, max 32768 bytes. Health must match workspace, r11 epoch/process/server
and native contract. It supplies its own `electron-r11-canary-output-reader`
identity and explicitly claims **no attestation**. It never creates a ChatWeb or
approved-patch bridge identity. This is authenticated local read-only observation;
the original execution's attested source binding still comes from the ledger.

The immutable public receipt contains top-level exact action/task/command/Job/
RUN/WAVE/proof/plan/runtime pins, `completed_at_ms`, observation hash and `stdout`
and `stderr` safe read-output projections. Each stream has content, content SHA,
exact command/output refs and retention counters. TAP must name the exact four
fixture cases with 4 pass / 0 fail; stderr must be empty, output complete and
untruncated. Root passes this receipt to the correlator for cross-checking against
the real durable Job and ProofLedger. It never constitutes semantic acceptance.

Offline reader tests: `node --test native-output-read.test.cjs` (no Electron,
credential access, HTTP or runtime effects).
