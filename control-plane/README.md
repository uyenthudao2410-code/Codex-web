# Coding Tools Control Plane

This is the first deployable source slice for the Ubuntu control plane. It is a
single-owner, SQLite-backed intake and dispatch service. It deliberately does
not execute local Coding Tools calls itself: a registered node must authenticate,
admit the action under its existing local authority, and return a receipt.

## Run locally

Set a random operator token of at least 32 characters outside the repository,
then run:

```powershell
$env:CONTROL_PLANE_OPERATOR_TOKEN = '<secret>'
$env:CONTROL_PLANE_DB = "$PWD/var/control-plane.sqlite3"
# Optional deployment metadata: the exact Git revision selected by the
# operator's deployment procedure, not a substitute for process/byte proof.
$env:CONTROL_PLANE_DECLARED_SOURCE_REVISION = '<40-or-64-hex-git-revision>'
# Leave unset unless the private HTTPS Tailnet origin and reverse proxy have
# been selected and verified. Setting this enables the browser operator UI.
$env:CONTROL_PLANE_WEB_ORIGIN = 'https://<private-tailnet-control-plane>'
python -m control_plane
```

The default listener is `127.0.0.1:8765`. Do not bind a public address until a
network and TLS/authentication boundary has been explicitly configured.

## Ubuntu root MCP ingress and OpenAI Tunnel

The production launcher starts two listeners in one process:

- `CONTROL_PLANE_BIND:CONTROL_PLANE_PORT` is the private Tailnet-facing
  operator UI and node/API listener. In production it has **no** `/mcp` route.
- `127.0.0.1:${CONTROL_PLANE_MCP_PORT:-8766}` is a dedicated, loopback-only
  root MCP ingress. It accepts only `POST /mcp`; UI, health, enrollment,
  admin, node, and browser routes return `404` there.

The OpenAI Tunnel service template receives the second listener only. This
prevents an MCP tunnel profile from becoming a proxy for the private console
or node control API. It does not grant the Tunnel client operator authority:
`/mcp` still requires a short-lived, server-issued context-scoped grant.

Create the Linux `tunnel-client` profile manually using the current official
[Secure MCP Tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).
The profile must use exactly
`http://127.0.0.1:<CONTROL_PLANE_MCP_PORT>/mcp`; run
`tunnel-client doctor --profile <profile> --explain` before enabling
`codex-control-plane-mcp-tunnel.service`. Keep the runtime API key in the
protected tunnel-client profile/init flow, never in this repository, SQLite,
the control-plane environment file, or a service command line. The service
only runs `tunnel-client run --profile <profile>` and validates that the named
Tunnel ID and client binary are present in the protected environment.

After the verified candidate has started the loopback listener, the operator
creates that named HTTP profile in a private terminal. The current official
client flow uses `CONTROL_PLANE_API_KEY` only for `init`; replace the
placeholders locally and clear that shell variable immediately afterwards:

```bash
export CONTROL_PLANE_API_KEY='<runtime-api-key-entered-locally>'
tunnel-client init \
  --profile ubuntu-root-mcp \
  --tunnel-id 'tunnel_<ubuntu-root-mcp>' \
  --mcp-server-url 'http://127.0.0.1:8766/mcp'
unset CONTROL_PLANE_API_KEY
tunnel-client doctor --profile ubuntu-root-mcp --explain
```

This creates no public endpoint and must happen on Ubuntu, never a Windows
executor. The later systemd service only uses the protected profile. Record
the selected binary version/checksum and the content-free `doctor` result in
the deployment receipt; do not paste its credential-bearing profile anywhere.

Do not activate this service against a Windows Tunnel ID. First stop/fence the
old owner through the approved cutover procedure, then initialize one new or
explicitly transferred Ubuntu profile. A live `tunnel-client` health/ready
surface and an actual supported OpenAI-product MCP call are required evidence;
a Tailnet `curl` to `/mcp` or `/healthz` does not prove the Tunnel path.

`CONTROL_PLANE_HEALTH_EXPECTED_ADMISSION` is a required, observation-only
healthcheck expectation. Set it to `recovery` while intake/dispatch is
deliberately closed for migration or a canary; set it to `open` only after the
separate readiness review explicitly opens admission. This variable never
changes admission. A healthcheck pass in `recovery` proves planned maintenance,
not execution readiness.

## Private browser operator UI (source capability, not a live deployment claim)

The browser UI is **disabled by default**. It becomes available only when
`CONTROL_PLANE_WEB_ORIGIN` is one canonical HTTPS origin with no path, query,
or credentials. This value must name a private Tailnet HTTPS reverse-proxy
origin chosen by the operator; the Python server itself remains the HTTP
upstream. Do not set it to `http://100.116.112.22:8765`, a public/Funnel URL,
or a guessed hostname.

Before enabling it on a named host, the change record must identify the exact
private HTTPS URL, certificate/proxy owner, listener, service environment file,
and rollback action. Verify that the proxy forwards only to the intended local
control-plane listener, that it is unreachable from the public Internet, and
that a browser receives the expected certificate before entering an operator
token. This source change neither provisions a proxy nor restarts a service.

With the explicit origin configured, `GET /` and the two fixed assets serve a
small Vietnamese operator console. Login exchanges the operator token for a
process-local 30-minute cookie (`HttpOnly; Secure; SameSite=Strict; Path=/`);
sessions disappear on service restart and logout invalidates the session. The
token is never stored in URL, localStorage, sessionStorage, asset bundle, node
configuration, or service log. Login attempts are rate-limited in memory per
direct peer address. A proxy that hides all clients behind one address will
therefore share that small single-owner rate limit unless an approved trusted
proxy design adds a separately validated client identity.

The UI requires the configured exact `Origin` and session-bound
`X-Control-Plane-CSRF` value for writes. It can approve an existing pending
enrollment (identity only); create an opaque workspace binding for an approved
node; issue a 5-minute to 24-hour, server-clock context; close a context or
revoke a binding; close central admission to `recovery`; and queue only the
fixed `workspace_context` read-only canary for one already-live context. It
cannot create an enrollment, choose a tool/arguments/path, create a policy,
grant a node credential, open admission, or execute an action. Queue
acceptance is not local execution or a completed effect. Reopening remains an
explicit operator-runbook action through the existing Bearer surface after
independent readiness/inflight review.
Closing admission blocks new central intake/dispatch; it does not stop a
Windows job or prove an existing effect has not happened.
The overview is an authenticated, no-store central read model. It exposes a
bounded action/receipt lifecycle (delivery state, latest receipt state/time and
count) so an operator can distinguish queued, uncertain, accepted and terminal
states; it intentionally omits raw work objectives, criteria, scopes, action
arguments, receipt payloads, credentials, and local handles. It does not create
a shell route, select a Windows path, issue a node command, or infer local
execution from a heartbeat.

Each node can additionally report one compact **local policy observation** with
its heartbeat: `enabled`, `expired_or_disabled`, or `unavailable`, plus a safe
expiry or reason code. It is node telemetry only—not a browser-granted right or
proof that central policy validation succeeded. The browser overview omits the
policy digest, policy file, local workspace path, and every credential; old
nodes that omit this field retain their last observation rather than being
shown as a fabricated new state.

Static routes are an exact allowlist with CSP, no-referrer, no-frame, nosniff,
and no-store headers. The dashboard uses `textContent` for observations and
polls a single central overview about every five seconds only while visible; it
does not invoke SSH, `systemctl`, or process census during a browser refresh.
The following proof must still be collected after an authorized deployment:

1. private HTTPS URL/certificate and non-public reachability;
2. configured origin and expected package fingerprint in the protected service
   environment, followed by a controlled restart and health receipt;
3. browser login/logout/session expiry and CSRF rejection over the real HTTPS
   origin; and
4. fresh central/node observations and the packaged Windows RC-A canary.

## Current API boundary

- `GET /healthz` is unauthenticated and reports service/SQLite health, durable
  schema/admission mode, a process-lifetime `service_instance_id`, a
  `package_source_sha256` calculated from the immediate `control_plane/*.py`
  files at process startup, and an optional operator-declared Git revision.
  The instance ID supports restart correlation; the package fingerprint is
  content-free evidence to compare with the selected deployment artifact.
  Neither value nor the declared revision proves service ownership,
  configuration, or an external checkout receipt. Operators must compare all
  three with the service/unit/check-out evidence.
- A SQLite read/write/commit error on this HTTP surface returns the typed,
  content-free `503 DURABLE_STORAGE_UNAVAILABLE`; it never returns a successful
  acceptance for that failed request. The response deliberately excludes the
  database error text, host path and transaction details. Operators still need
  a recovery/space/ACL investigation before retrying an interrupted operation.
- An operator can set `CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256` in the
  protected service environment to the selected artifact's exact health
  fingerprint (`sha256:<64 lowercase hex>`). Startup fails closed before
  binding the listener if it is malformed or differs from the installed
  package. Health reports that expected value only after the equality check;
  this is a package comparison gate, not a substitute for an artifact signature
  or service/unit ownership proof.

Before deployment, calculate the expected value from the exact checkout or
package directory selected for deployment without opening SQLite or starting a
listener:

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.maintenance package-fingerprint
```

The content-free receipt has `operation=control_plane_package_source_fingerprint`
and `package_source_sha256`. Copy only that fingerprint into the protected
environment for the service that will run the same package. A later health
match proves package comparison at startup; it does not prove the systemd unit,
checkout selection, secret handling, node authority or a task effect.

After the selected artifact has been deployed through an authorized procedure,
an operator can make one **read-only** comparison against its credential-free
`/healthz` URL. The verifier requires the reported package fingerprint and the
server's protected startup-gate value to equal the exact selected-package
receipt, plus current schema, durable admission, SQLite health and a
well-formed process instance ID. It emits no endpoint, health body, exception
text or credentials. A missing field is a typed fail-closed result rather than
evidence that an older server matches the selected artifact.

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.deployment_verifier `
  --health-url 'https://<private-control-plane>/healthz' `
  --expected-package-source-sha256 '<sha256-from-selected-package-receipt>' `
  --expected-admission open
```

This command does not authenticate, start/stop/restart/deploy a service, open
SQLite, change admission, inspect a systemd unit, or issue any execution
request. Its pass result is a single health-response comparison at that time,
not an artifact signature, trusted service-owner/configuration/checkout proof,
write-admission proof, binding proof, or canary.

## Versioned Ubuntu release artifact

Build the Ubuntu artifact from a clean selected checkout (runtime-only
`.coding-tools` evidence is excluded from the artifact and may continue to
change):

```bash
npm run dist:control-plane
```

The command writes a new `dist/codex-control-plane-<revision>/` directory and
matching `.tar.gz` archive. Each contains the Python backend and embedded Web
UI, versioned systemd service/timer templates (including the separate root MCP
Tunnel unit), release-local backup and health
scripts, a secret-free environment example, `DEPLOYMENT.md`, and a manifest
with source revision, package fingerprint and per-file/component hashes. It
refuses to overwrite an existing release output or build from source drift.

Before making an extracted release the `current` target, run its own
content-free verifier and compare the receipt to the selected manifest:

```bash
python3 <release-dir>/deploy/control-plane-verify-release.py --release-dir <release-dir>
```

The verifier rejects a changed, missing, extra, symlinked, or malformed release
file before any service action. It is an artifact-integrity check only; it does
not prove that the selected release is loaded by systemd or authorize activation.

Neither artifact contains the SQLite database, operator token, node credential,
session, backup, or real environment file. Creating it does not change the
`current` release symlink, systemd units, service, admission, or a Windows node.
- A node can post `/v1/enrollment-requests` with a hash of its locally-generated
  secret. The operator lists and approves that exact request; the secret never
  crosses the network or enters Git.
- `POST /v1/nodes/enroll` remains an operator-only bootstrap path; it returns a
  per-node credential once, which must be placed in protected configuration.
- `POST /v1/bindings`, `/v1/contexts`, `/v1/work-requests`, and `/v1/actions`
  require the operator bearer token.
- Operator-only `GET /v1/nodes`, `/v1/contexts`, and `/v1/work-requests`
  provide owner-scoped inventory. Their `/{id}` forms provide one node/context
  or a request with non-payload action lineage; node credentials, action
  arguments, and admission references are not included in these list/request
  observations. `GET /v1/actions/{action_id}` remains the owner-only detailed
  action, attempt, receipt, and any immutable reconciliation observation
  endpoint. It is never an execution endpoint.
- Operator-only `POST /v1/nodes/{device_id}/rotate-credential` rotates the
  node credential and increments its recorded generation; the returned secret
  is shown once and belongs only in protected node configuration. Operator-only
  `.../revoke`, `/v1/bindings/{binding_id}/revoke`,
  `/v1/contexts/{context_id}/close`, and
  `/v1/work-requests/{request_id}/cancel` block new admission and terminally
  refuse only queued, never-sent actions. They do not call a remote process,
  overwrite a possible effect, or pretend a sent action has stopped.
- Operator-only `GET`/`POST /v1/maintenance/admission` exposes and changes the
  durable central admission mode between `open` and `recovery`. Recovery blocks
  new action sealing and polling but keeps authenticated late receipts available
  for reconciliation; reopening is an operator decision, not proof that a
  restore is safe or that a node-side effect has stopped.
- `POST /v1/nodes/{device_id}/heartbeat`, `/poll`, and `/receipts` require the
  node credential. A queued action is returned at most once by this source
  slice, only after one transaction rechecks that the node is `ready`, has a
  fresh heartbeat (60 seconds by default), reports real runtime/epoch/contract
  identities, and still matches live binding/context/request/expiry state.
  A stale or non-ready node leaves the action queued; revoked, changed, or
  expired authority is terminally refused without delivery.
- Polling writes `dispatch_unconfirmed` and returns an exact `attempt_id` before
  the response. Every receipt must bind that attempt. Exact duplicate receipts
  return their original durable acknowledgement; `unknown` becomes
  `reconcile_required` and is not redelivered. `accepted` and `completed`
  receipts require a non-empty local handle, while a later terminal receipt is
  required to settle an accepted or unknown action.
- A protected operator may use
  `POST /v1/action-reconciliations/quarantine-historical-unknown` (or the
  same-origin browser equivalent) only for exact `workspace_context` actions
  on one selected node that remain `reconcile_required` with a latest
  `unknown` receipt. It requires the literal declaration
  `HISTORICAL_READ_ONLY_UNKNOWN_EFFECT`. The result stores an owner/device-bound
  `quarantined_unknown` disposition, receipt/evidence digests, timestamp and an
  audit event. It does **not** alter receipts or delivery state, settle the
  action, permit redelivery, or claim that a workspace was untouched or read.
  Backup inspection reports both all unresolved actions and the smaller count
  still unquarantined; the healthcheck may pass only when the latter is zero.
- `POST /mcp` is a stateless JSON-RPC façade for MCP `2025-11-25`, reachable
  only with a **server-issued MCP access grant**, not the operator Bearer.
  An operator creates a grant through `POST /v1/mcp-access-grants` for exactly
  one live `context_id`, an identified external principal, and an expiry no
  later than that context. The raw bearer is returned only by that create
  response; SQLite retains a domain-separated digest, authenticated grant
  metadata is redacted by `GET /v1/mcp-access-grants`, and an operator can
  immediately revoke it through `POST /v1/mcp-access-grants/{grant_id}/revoke`.
  A revoked/expired grant, closed context, or revoked binding/node cannot call
  `/mcp`. Caller headers and request fields cannot select another context.
  This is the credential intended for the Ubuntu-owned Tunnel/controller after
  its ingress deployment gate, not a Windows node credential or a way to give
  an external client the operator token.

  The façade declares exactly the eight public `smart-v3` tool names and an
  explicit control-plane `context_id` envelope; this is not a byte claim about
  the Windows tools' local input schemas. `workspace_context` defaults to
  context-scoped **central** target/node status with
  `workspace_accessed=false`. An optional existing `action_id` under that
  context normally adds a redacted lifecycle projection (action/attempt/receipt
  IDs, state and digests only). If, and only if, that exact action has a
  completed receipt for the current façade contract, it also returns a bounded
  metadata-only summary: project type/name/version, at most one root entry and
  compact Git state. It never returns action arguments, raw receipt payloads,
  local handles, paths, file contents, task text, or symlink targets. Its
  explicitly named `request_read_only` operation accepts
  only an exact `context_id`, expiry, idempotency key, and the exact façade
  `{schema_version,profile,sha256}` advertised by `initialize` or `tools/list`.
  It atomically seals the fixed `workspace_context({detail:"compact",max_entries:1})`
  central intent/action with that contract pin. A drifted or malformed pin
  fails before durable intake. It still cannot call a node or grant local
  authority. Every
  other public tool
  returns the typed `LOCAL_ADMISSION_BRIDGE_REQUIRED` result until a separate
  local admission bridge and façade relay scope are accepted. The façade does
  not forward the client token or request body to a node, poll, or execute
  anything.

This is a bounded asynchronous central read relay, not a Windows local-MCP
execution adapter or a general end-to-end MCP proxy. The node's separately
named local admission lane must independently pass its policy, strict-runtime
and actor gates before a completed receipt can be observed. Mutation remains
blocked until a local adapter can pass the local authority gate. A grant alone
is never a file, process, local-policy, or task-approval authority.
Schema migrations are additive, source-versioned (current `user_version=10`),
and applied atomically by the store. `ControlPlaneStore.backup_to()` creates a
verified, non-overwriting SQLite Backup API snapshot when an operator calls it
explicitly. It is not an automatic startup backup and does not execute a
restore: before a verified restore/reconcile procedure, an operator must place
the service in its durable recovery admission mode. Retention, ACLs, and the
restore drill/runbook remain operational gates.

## Explicit verified snapshot

From an authorized maintenance shell on the host that owns the database, the
following command snapshots an **existing** database to a **new** destination.
It opens the source through SQLite read-only URI mode, so it neither creates nor
migrates the source DB; it verifies the destination's integrity and schema,
then reports a SHA-256 fingerprint of the staged snapshot bytes before the
atomic rename. Its success receipt intentionally contains no host paths or
credentials.

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.maintenance snapshot `
  --source '<existing-control-plane.sqlite3>' `
  --destination '<new-snapshot.sqlite3>'
```

The command does not start or stop the service, change central admission,
contact a node, copy secrets, or restore a snapshot. A missing source returns
typed `NOT_FOUND`; an existing destination returns `CONFLICT`. Keep the source
and snapshot outside the repository, apply OS ACL/retention policy outside this
command, and use an operator-approved restore/reconcile procedure before any
admission is reopened.

The detailed recovery/retention/drill contract is
[`docs/CONTROL_PLANE_RECOVERY_RUNBOOK.md`](../docs/CONTROL_PLANE_RECOVERY_RUNBOOK.md).
It deliberately distinguishes an isolated drill, a production restore, node
reconciliation, and admission reopen; the runbook does not grant any of them.

### Ubuntu automatic backup profile

For the single-owner Ubuntu pilot, the supplied
`deploy/codex-control-plane-backup.service.example` and `.timer.example` run a
verified SQLite Backup API snapshot **hourly**, with a randomized delay of up
to five minutes. `Persistent=true` makes a missed timer eligible on the next
user-manager start. The job refuses to run below **5 GiB** free space, writes
only owner-readable artifacts under the control-plane state directory, and
retains only its own automatic snapshots for **30 days**. It never prunes a
manual/pre-migration/recovery snapshot or any repository evidence.

Install the two user units only after confirming the deployment's selected
paths, then run one job explicitly and inspect its content-free receipt before
enabling the timer. The job's `last-automatic-backup.json` records the snapshot
and immutable-inspection receipts plus free space at capture. This backup does
not encrypt files by itself, prove off-host durability, perform restore, or
authorize admission reopening; retain the operational encryption and restore
requirements in the recovery runbook.

The companion `codex-control-plane-healthcheck` service/timer checks the
exact deployed package, schema, process instance, `open` admission and backup
freshness every 15 minutes. It writes a content-free `last-healthcheck.json`
only when every condition passes. A control plane intentionally held in
`recovery`, a bad/missing package gate, or a backup older than 2 hours 15
minutes exits non-zero for the user-unit journal; it does not restart anything
or reopen admission.

Before an operator considers a separately authorized restore, inspect the
completed snapshot by its receipt fingerprint:

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.maintenance inspect-snapshot `
  --source '<completed-snapshot.sqlite3>' `
  --expected-sha256 '<snapshot_sha256-from-receipt>'
```

Inspection opens the artifact with SQLite `mode=ro&immutable=1`; it rejects a
snapshot carrying `-wal` or `-shm` sidecars, a malformed/mismatched expected
digest, or failed integrity. Its content-free receipt returns the artifact
digest, schema, durable admission mode when present, per-state action counts,
the total count requiring reconciliation (`dispatch_unconfirmed`, `accepted`,
or `reconcile_required`), plus audited `quarantined_unknown` and still-
unquarantined counts. It does **not** restore files, start/stop the service,
change admission, contact nodes, reconcile effects, or determine that reopening
admission is safe.

When a separately authorized isolated-drill or restore procedure needs a
candidate from that inspected source, prepare a **new** file rather than
replacing a database:

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.maintenance prepare-recovery-restore `
  --source '<completed-snapshot.sqlite3>' `
  --destination '<new-recovery-candidate.sqlite3>' `
  --expected-sha256 '<snapshot_sha256-from-receipt>'
```

The source must be the current control-plane schema and carry a valid durable
admission value. The command first performs the same immutable inspection, then
creates a non-overwriting candidate with durable `admission_mode=recovery` and
a content-free event binding it to the source artifact hash. Its receipt returns
only hashes, integrity/schema, byte count and `recovery`; it omits host paths
and credentials. This prevents a historical `open` snapshot from silently
becoming dispatchable while it is being prepared. It does **not** replace any
live DB, stop/start a service, alter the running service's admission, contact a
node, reconcile effects, configure storage policy, or constitute a completed
restore. Follow the operator-approved procedure in the recovery runbook.

## Node enrollment without copying a server secret

Normal Windows onboarding is through the packaged Command Center in
`central_executor` mode: enter the HTTPS Ubuntu origin and select **Gửi yêu cầu
pairing**. It uses the installed node agent and the one Electron data root,
`%APPDATA%\web-mcp-assistant\control-plane-node.json`; the operator must still
approve the resulting enrollment on Ubuntu. It never asks for an OpenAI key,
Tunnel ID, operator bearer, or a workspace path.

The source command below is for an isolated development fixture only. HTTPS is
required away from loopback; do not substitute the Tailnet IP over HTTP:

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.node_agent request-enrollment `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --server-url https://svhome.tail0e4032.ts.net `
  --device-id <installed-device-id> `
  --endpoint-id <current-endpoint-id> `
  --display-name <installed-display-name>
```

Approve the returned enrollment ID on the server under the operator token. The
agent can then send a heartbeat. Its ordinary `poll` mode is deliberately
non-executing **and does not call the central dequeue endpoint**; this prevents
an unsupported client from allocating a `dispatch_unconfirmed` attempt without
a receipt. Only the separately named read-only lane below may receive an
action after its local admission checks pass.

To publish the Hub's *actual*, fail-closed status after the Windows user has
logged in, use the one-shot adapter below. It reports `ready` only when
`dev-ui-lifecycle.js status` proves the current installation, non-stale runtime
telemetry, matching current MCP disk/running revisions, no pending update,
`components_ready=true`, `fully_ready=true`, and a
`CURRENT_ACKNOWLEDGED` connector with current-process rediscovery. A compatible
activation bootstrap, pending update, missing identity, connector or admission
pending is `degraded`, not ready; a contradictory `state=MISSING` report stays
blocked even if positive flags are present. Only after that independent
aggregate predicate is strict, the adapter makes one allowlisted Recovery IPC
read, `runtime.identity_observation`. The read is bound to the exact
development installation and returns only a sanitized MCP process ID, server
ID, activation epoch, and tool-contract SHA-256. Both IDs, a matching current
epoch, and a valid SHA-256 are required before the central heartbeat can report
`ready`; the database stores the server ID separately and dispatch remains
closed for an unreported one. An unavailable, malformed, mismatched, or merely
compatible observation remains `degraded/runtime_identity_unproven`.

This observer is **not** a local execution actor. It has no action arguments,
does not call `tools/call`, and cannot grant permissions, restart the runtime,
patch files, or accept work. Ordinary `poll` remains non-executing and cannot
dequeue central work.

The separately named `poll-read-only-once` command is the first narrow local
admission lane in source only. It can act only after all of the following are
true: the independent Hub status is strict current-process-ready; the
descriptor-bound identity observation is exact; and Recovery Host finds an
explicit, locally installed, expiring policy at its data root. That policy is
absent by default, contains no credential, and must bind the server origin,
owner, local device, endpoint, workspace, generation, expiry, and the exact
central façade `{schema_version,profile,sha256}` pin. Policy schema v1 has no
such pin and is rejected rather than silently upgraded. The lane
admits exactly `workspace_context` with `{ "detail": "compact", "max_entries":
1 }`; it owns the local MCP token and attestation internally, uses the distinct
`electron-control-plane-bridge` actor, and never exposes either credential to
the Python node agent or central service. The bridge receipt must return the
same façade pin plus a bounded, independently hashed metadata-only workspace
summary before it can be accepted. A local journal is written before the
subprocess call; an interrupted prepared entry becomes an `unknown` receipt
instead of being retried. The poll command itself does not create a policy,
binding, context, or action; it can only complete a prior sealed intent, and is
not a scheduler, logged-out Windows service, mutation lane, or live-canary
result.

After the explicit policy has been installed and its local ACL reviewed, an
operator may run a **bounded, logged-in** loop locally. It first verifies that
the enabled, unexpired policy still matches this node configuration's central
origin/device/endpoint; on failure it does not heartbeat or dequeue. Each
iteration then publishes a fresh strict runtime heartbeat before the one
read-only poll. The process has no scheduler installer, cannot run longer than
24 hours, and must be started deliberately again after logout/reboot.

```powershell
# One hour at a 60-second cadence; do not run this before the explicit policy
# installation and Windows ACL gate above have been completed.
& '<installed>\resources\resources\control-plane\node-agent.cmd' run-read-only-loop `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --interval-seconds 60 `
  --max-iterations 60
```

The loop prints only bounded lifecycle summaries. A degraded runtime or
transport error is recorded for that iteration and never authorizes a retry of
a possible local effect; an interrupted prepared bridge entry remains an
`unknown` receipt as with the one-shot lane.

### Long-lived same-user read-only agent

After the packaged node has a reviewed, explicit policy, the named
`run-read-only-agent` entrypoint is managed by the existing **same-user
Recovery Supervisor** in a newly installed candidate. The Supervisor verifies
the packaged Python and agent hashes from its manifest, then starts it only
when the private node configuration and an enabled, unexpired, matching local
policy exist. An older supervisor manifest has no agent fields and remains
`manifest_legacy`; it never guesses an agent path or starts one. Unlike the
bounded diagnostic loop, the agent runs until the local operator stops it or
its policy becomes unavailable. It is still only the allowlisted
`workspace_context` bridge: it does not receive a Tunnel ID, Runtime API key,
arbitrary command, patch, or write permission.

Every iteration revalidates the locally stored policy *before* publishing a
heartbeat or polling the central queue. A disabled, expired, malformed, or
wrong-node policy therefore stops the agent rather than generating repeated
rejections. Runtime and network failures use bounded exponential backoff; they
never repeat a possible local bridge effect. One atomically-created lock next
to the private node configuration prevents two same-profile agents from
dequeueing concurrently. A lock is reclaimed only when its recorded PID is
confirmed dead; malformed or uncertain locks remain fail-closed for local
operator review.

```powershell
# The packaged same-user Supervisor starts this exact command after local
# policy onboarding. Running it manually is only for focused diagnostics. The
# command does not install another Scheduled Task and does not support
# logged-out Windows or Session 0/SYSTEM execution.
& '<installed>\resources\resources\control-plane\node-agent.cmd' run-read-only-agent `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --interval-seconds 15 `
  --max-backoff-seconds 300
```

`--max-iterations` is a focused diagnostic/test bound only; the default `0`
means the supervisor owns the process lifetime. Do not use the agent as proof
of central mutation, unattended boot, or a complete Windows onboarding flow:
those gates require the separate pairing, lifecycle and authority proof.

### Explicit packaged read-only policy installation

The normal candidate workflow is: Ubuntu operator approves the node, creates
an opaque binding, issues a live context, then the same Windows user pastes the
`ctx_…` value into Command Center and selects **Cài policy read-only**. Electron
starts its packaged node agent only after that local click. The agent
authenticates itself to Ubuntu; Ubuntu returns a template only for that exact
live context, device and endpoint. It derives owner/workspace/generation/
expiry/facade contract from the server response, rather than accepting them
from the Windows UI. No OpenAI key, Tunnel ID, operator bearer, node secret,
Windows path, or workspace content is put in the UI or receipt.

For break-glass diagnostics where Command Center cannot be used, the equivalent
installed command accepts only the context ID and still requires local
confirmation. It is not an auto-enrollment side effect. The launcher fixes
bundled Python, installed Electron tree, packaged runtime mode and
`%APPDATA%\web-mcp-assistant`; it does not use a source checkout or global Node.
Do not copy a policy between nodes. Omit `--replace` unless the logged-in user
has deliberately selected a replacement context.

```powershell
# Run only on the logged-in Windows pilot node. The installed launcher supplies
# --runtime-mode packaged, --project-root and --node itself.
& '<installed>\resources\resources\control-plane\node-agent.cmd' install-read-only-policy-from-context `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --context-id 'ctx_<issued-by-ubuntu-console>' `
  --confirm-install

# Credential-free local observation, then an explicit local fail-closed stop.
& '<installed>\resources\resources\control-plane\node-agent.cmd' inspect-read-only-policy
& '<installed>\resources\resources\control-plane\node-agent.cmd' disable-read-only-policy --confirm-disable
```

The install command refuses a missing confirmation, closed/expired/wrong-node
context, an over-24-hour policy, malformed server template, an already existing
policy without `--replace`, or a caller-supplied packaged data root. It returns
only a policy contract SHA, expiry, runtime mode and
`windows_acl_verified=false`; that last field is intentional. Windows ACL
ownership must be inspected during the install gate and cannot be inferred from
Python `chmod`. Disabling writes a disabled policy instead of deleting it,
preserving local evidence while making Recovery Host reject the bridge. The
command never starts a scheduler, invokes the bridge, dequeues central work,
changes a binding/context/action, or grants mutation authority.

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.node_agent runtime-heartbeat `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --project-root "$PWD"
```

This command does not execute a remote action and does not make Electron work
while Windows is logged out. It may later be called by a logon-scoped scheduler
only after the interactive-runtime availability design has its own proof.

When it receives a complete authenticated heartbeat echo, the node agent writes
the credential-free `control-plane-route-evidence.json` beside the Electron
data root. Electron accepts it only for its own stable device ID and only for
60 seconds; a malformed, future, stale, copied-to-another-device, or missing
record leaves central routing unavailable. The evidence contains the central
origin, endpoint ID, credential generation, timestamps and policy state—never
the node secret, workspace path, or an action grant. In `central_executor`
mode, this is the replacement readiness proof for a **Windows OpenAI Tunnel**:
it proves a recent authenticated node-to-Ubuntu path, not that a Tunnel runs on
Windows. A locally enabled policy is still required before the narrow
read-only lane can be ready, and each action is admitted again by Recovery
Host. It is therefore not evidence of generic write/exec authority.

## Focused proof

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m unittest discover -s control-plane/tests -v
node --test control-plane/tests/recovery_identity_observer.test.cjs
node --test control-plane/tests/recovery_read_only_bridge.test.cjs
```
