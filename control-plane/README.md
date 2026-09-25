# Coding Tools Control Plane

This is the first deployable source slice for the Ubuntu control plane. It is a
single-owner, SQLite-backed intake and dispatch service. It deliberately does
not execute local Coding Tools calls itself: a registered node must authenticate,
admit the action under its existing local authority, and return a receipt.

## Shared ChatGPT account and workspace binding

One bind creates an opaque `binding_id` that selects a registered device,
endpoint, workspace and generation. ChatGPT clients using the same verified
OAuth principal may select that ID; the client is only the controller and does
not become the execution host. Each task pins
`{binding_id, device_id, endpoint_id, workspace_id, workspace_generation}` and
the Windows runtime keeps the files, Git, processes and OS-local permissions.
Ubuntu authenticates, routes and records receipts; it does not ask for a new
context or per-command approval inside the standing local scope.

The OAuth inventory is lifecycle-aware. Each opaque target includes
`binding_state`, `node_state`, `workspace_state`, `dispatch_state`, and the
content-free `dispatch_blockers` list. A revoked binding or retired workspace
generation remains visible to the same linked account so another client can
show the real state; `task_open` and action admission still reject it. The
inventory never contains an absolute path, node secret, OAuth subject, or
context, and it never silently fails over to another binding.

The current implementation status and reuse/gap matrix are maintained in
[`docs/TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md`](../docs/TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

## Run locally

Set a random printable-ASCII operator token of 32–512 characters outside the repository,
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
or node control API. It does not grant the Tunnel client operator authority.

There are three explicit MCP authentication modes:

- `legacy_context_grant` is the current transition/default mode. `/mcp`
  requires one short-lived server-issued, context-scoped grant, and the Tunnel
  launcher receives an owner-private header-file reference for that grant.
- `oauth_introspection` is the account mode. The resource server validates
  each client-provided OAuth **access token** using its configured,
  authenticated introspection endpoint, then resolves a separately linked
  `(issuer, subject)` principal. There is no fallback to a legacy `mcp_…`
  bearer and the Tunnel launcher must not receive or inject an Authorization
  header. The default OAuth surface is inventory/task discovery only; the
  trusted-workspace profile below explicitly opts into standing local write and
  structured exec after its distinct scope, node policy and package gates pass.
- `private_tunnel_service` is an explicit, shared Business-connector mode for
  owners who permit every member of that connector to use the same bounded
  workspace authority. The Tunnel injects a revocable, server-issued service
  grant from an owner-private header file; Ubuntu records one service principal,
  not a verified ChatGPT user. It must never be described as per-user OAuth.
  The owner provisions and revokes this principal/grant through the protected
  operator API. File read, standing patch and structured exec are separate
  startup flags and remain bounded by current binding, workspace generation,
  node-local policies, exact contract, lease and receipt checks. A grant alone
  never changes Windows permissions or opens central admission.

The shared service principal is not a ChatGPT Business member identity. Its
grant scopes are exactly `control-plane.inventory`, the separate
`control-plane.read` for content/task operations, and `control-plane.patch`
for writes/command output; a new patch grant must also include read. Changing
service configuration cannot upgrade an old grant. Existing inventory-only
grants stay inventory-only after migration, and old `[inventory, patch]` grants
cannot work under the new read gate: revoke/rotate them instead of treating
their stored scope as upgraded. The service may create a task or action only
for one unexpired, exact
`scoped_pilot` decision naming its principal and binding. This remains true if
global admission is later set to `open`. The decision can be created only in
`recovery`, after reconciliation finds no unresolved prior delivery on that
node. Switching to `scoped_pilot` is a separate bearer-operator runbook step;
the private browser Console can only close admission or revoke a grant or
decision. A revoked/expired decision stops new intake and polling, not an
already-dispatched Windows effect. Restore candidates force `recovery`.

The packaged Windows Command Center can install standing file-read and
exact-patch policies for the locally selected registered workspace generation
after an authenticated node obtains the current facade contract from Ubuntu. It
also has a fail-closed exec-policy installer: it requires the exact registered
workspace/generation, central `exec_enabled` authority and a passing
workspace-bound Windows Sandbox child-process probe before installing and
re-observing the local policy. Exec confinement comes from the Windows Sandbox
VM's exact read-write workspace share, read-only toolchain shares and guest
network lockdown—not from `cwd` or an argv prefix. Never enable the service
exec flag or claim live command confinement from source or dev-candidate proof
alone. The current deployed state remains exec-disabled until the exact
packaged Windows runtime, Ubuntu grant/binding and local policy are all
independently observed.

For a controlled source-candidate rollout, keep this order (none is performed
by editing the example environment file):

1. Snapshot/verify the current Ubuntu database, reconcile historical
   unconfirmed actions, and keep admission in `recovery`. Record exact package,
   service instance and schema before changing the service. The private
   Console may display decisions and revoke them, but cannot reopen admission.
2. Deploy the verified Ubuntu candidate with the MCP listener bound to
   `127.0.0.1`; select `private_tunnel_service`, `FILE_READ_ENABLED=true`,
   `STANDING_WRITE_ENABLED=true`, `EXEC_ENABLED=false`, and the fixed inventory
   and patch scope names. Do not expose the operator API through the tunnel.
3. Via the authenticated operator API, create one service principal, then a
   short-lived grant with exactly `[control-plane.inventory,
   control-plane.read, control-plane.patch]`. The raw token is returned once;
   write its full `Bearer …` header directly to an owner-private 0400/0600
   file outside the release/repository, never to chat, shell history, logs or
   the browser Console. Point only the Ubuntu Tunnel launcher at that file.
   Revoke an old grant after a replacement has been verified; grants expire
   within 30 days. After the exact pilot is accepted, enable the bounded
   authority-renewal service/timer with its protected operator environment.
   It may extend only a still-live grant and decision, never create a bearer,
   change a binding, or reopen admission; an expired/revoked record still
   requires the operator runbook to provision a replacement.
4. On the packaged Windows app, select/re-register the exact root with
   `read=true, write=true`. Replacing a read-only registration creates a new
   generation and retires its old bindings/tasks/policies. Create a new Ubuntu
   binding for that exact generation, then use Command Center to install and
   re-observe the standing file-read and patch policies. Merely ticking
   `write`/`exec` is not proof of an installed policy.
5. The bearer operator creates a `POST /v1/scoped-pilot-decisions` record with
   that service `principal_id`, exact `binding_id`, expiry no more than 24
   hours ahead and an audit reason, then separately sets admission to
   `scoped_pilot`. This is one target decision, not approval of each patch.
   Read back `/v1/maintenance/admission` and the decision before canaries.
6. Verify Tunnel health and `doctor`, refresh the ChatGPT connection metadata,
   start a new conversation, and perform one selected-target inventory/read,
   one exact existing-file patch, receipt readback and stop/replay canary. Do
   not claim completion from `node.ready` or `workspace_accessed=false` alone.
7. Enable service `EXEC_ENABLED` and install Windows exec policy only after the
   exact packaged runtime has passed its workspace-bound Sandbox canary, the
   same workspace generation has central `exec_enabled` binding authority, and
   the installed policy readback matches its allowlist fingerprint. Candidate
   `r8` has packaged Node/npm proof only; it is not an installed/live exec
   acceptance. Closing admission or revoking the decision blocks new intake/poll
   but cannot undo in-flight effects.

In OAuth mode the dedicated MCP listener alone serves
`GET /.well-known/oauth-protected-resource`; every other GET route remains
404 there. A missing or invalid token receives both a standard
`WWW-Authenticate` challenge and the MCP `mcp/www_authenticate` result
metadata for `tools/call`. OpenAI clients need this metadata, per-tool
`securitySchemes`, and the runtime challenge to start account linking. The
authorization server is external to the private Tunnel: it must expose its
own reachable HTTPS discovery, authorization, and token endpoints and support
the exact callback shown by the OpenAI connection configuration. See the
official [OpenAI Authentication guide](https://developers.openai.com/plugins/build/auth).

The MCP OAuth ingress intentionally does not apply the private Console's
cookie/CSRF same-origin rule. A remote client may send its own `Origin`; the
resource server still requires a verified OAuth bearer and linked principal on
every protected request, and it emits no CORS permission merely because an
`Origin` header is present.

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

The Ubuntu tunnel launcher treats repeated HTTP 401 `account_deactivated`
poll failures as a permanent credential failure. After three consecutive
signals it records a mode-0600 marker keyed to that exact Tunnel ID, stops the
client, and exits successfully so systemd does not retry the locked
credential. Restarting the same tunnel remains blocked; an operator must
restore that account or configure a separately allowed Tunnel ID and profile.
The launcher never switches accounts or credentials automatically.

Do not activate this service against a Windows Tunnel ID. First stop/fence the
old owner through the approved cutover procedure, then initialize one new or
explicitly transferred Ubuntu profile. A live `tunnel-client` health/ready
surface and an actual supported OpenAI-product MCP call are required evidence;
a Tailnet `curl` to `/mcp` or `/healthz` does not prove the Tunnel path.

When the candidate switches to `oauth_introspection`, put the same nonsecret
`CONTROL_PLANE_MCP_AUTH_MODE=oauth_introspection` in both protected service
environment files, configure all `CONTROL_PLANE_MCP_OAUTH_*` values only in
the control-plane service environment, and remove
`CONTROL_PLANE_MCP_AUTH_HEADER_FILE` entirely from `mcp-tunnel.env`. The
launcher fails closed if that old setting is even present. The introspection
client file must be an absolute, owner-owned, non-symlink regular JSON file
with mode `0400` or `0600` and exactly `client_id` and `client_secret`; it is
not the Tunnel Runtime API Key and must not be loaded by the Tunnel unit.
The selected IdP introspection response must identify an active `Bearer`
**access token**; an ID token or another token type is rejected even if its
other claims happen to look plausible. Its `exp` value must be finite and
future-dated, and any `nbf` value must already be in effect.

`CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED` is an optional **candidate** gate
that is valid only in `oauth_introspection` mode. It defaults to false and
must remain absent in `legacy_context_grant` mode. Setting it to true changes
the discovered facade contract to add only the separately policy-bounded,
read-only `workspace_context(read_file)` lane. It does not enable a write,
shell, arbitrary path, context, or local policy; the exact Windows root,
generation, allowed relative paths, byte/line caps, expiry and local approval
are still checked independently at the node.

`CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED` is a separate **C4
candidate** gate. It is accepted only in `oauth_introspection` mode when the
C3 file-read candidate is also explicitly enabled. It changes the discovered
contract to expose only `request_permissions(request_patch/status)`: an OAuth
caller can bind one proposed single-file patch to an opaque target, relative
path, preimage digest, patch digest, validation profile and short expiry. The
private Ubuntu Console may approve or reject that exact scope through its
existing session, Origin and CSRF protection. Approval is durable central
evidence only; it does not create an action, delivery attempt, local policy,
write relay, shell/process permission or Windows effect. Any future local
mutation bridge must independently compare the immutable scope and its own
current local policy before it may execute anything.

For the trusted-workspace account contract, the central source also supports a
separate standing-write candidate. Enable it only together with OAuth file-read
and a distinct write scope:

```text
CONTROL_PLANE_MCP_AUTH_MODE=oauth_introspection
CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED=true
CONTROL_PLANE_MCP_OAUTH_STANDING_WRITE_ENABLED=true
CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE=control-plane.patch
CONTROL_PLANE_MCP_OAUTH_APPROVED_PATCH_ENABLED=false
CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED=true
```

With this profile `agent_workflow.apply_patch` does not require a
`permission_request_id`. It still requires the authenticated account's
dedicated write scope, an explicit `binding_id` and `task_id`, current writer
lease/generation, exact relative path and preimage/patch digests, the sealed
Write Exact File envelope, and the current facade contract. The central store
only queues the action; the enrolled node must admit it under its standing local
workspace policy and operating-system permissions before writing. The action
TTL protects the queue from replay and is not a replacement for the node's
long-lived local policy. The HTTP→node completed/status and stale-generation
fixture is source/focused proof; standing lost-ACK/duplicate-effect/reconcile
proof, the exact Windows package, and live multi-client acceptance remain open.

Do not change a live service just by switching the mode variable. Complete a
candidate rollout first: configure an IdP that supports OAuth authorization
code + PKCE `S256`, exact issuer/resource/audience/scope validation, create a
private owner-only introspection-client JSON file, then prove discovery and
empty/nonempty account inventory through a supported OpenAI client.

For ordinary onboarding, a verified but unmapped OAuth account creates exactly
one opaque pending account-link request. It gets neither inventory nor a
context, policy, action, or local effect. The Ubuntu owner opens the private
Console and explicitly approves or rejects that request using its existing
session, Origin, and CSRF checks. The Console and its projections expose only
opaque request/principal IDs, state, and timestamps: never issuer, subject,
email, token, or workspace. Approval creates the owner mapping; it is
idempotent for the request but must not silently re-enable a later revoked
principal. The raw private OAuth-principal route remains only a controlled
bootstrap/recovery path, not the normal user onboarding flow. Provider subjects
are stored only as domain-separated digests; never put an access token or
subject value in a ticket, terminal history, or Git artifact.

`CONTROL_PLANE_HEALTH_EXPECTED_ADMISSION` is a required, observation-only
healthcheck expectation. Set it to `recovery` while intake/dispatch is
deliberately closed for migration, or to `scoped_pilot` while a bounded
exact-target pilot is the intended admission state; set it to `open` only after
the separate readiness review explicitly opens admission. This variable never
changes admission. A healthcheck pass in `recovery` proves planned maintenance,
and a pass in `scoped_pilot` proves only that the selected pilot state is
observed, not execution readiness.

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

The server validates a submitted operator credential's JSON type, ASCII
encoding, and byte length before the constant-time comparison. Empty,
oversize, Unicode, whitespace/control-character, and non-string values all
receive the same generic authentication failure; no credential value or
internal comparison exception is returned.

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

For the trusted workspace profile, the node first observes the enabled
standing `file-read`, `approved-patch`, or structured `exec` lane that matches
the current local workspace generation. In that case the reported expiry is a
60-second heartbeat-freshness bound, not a fabricated expiry for the standing
policy itself. The legacy compact read-only policy remains a compatibility
fallback only. A malformed, mismatched, or unregistered standing lane never
becomes route authority, and each action still rechecks its own local policy.

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

Before changing `current`, bind the selected manifest identity to both
operator-owned configuration files with the release-local helper. Run the
read-only check first, then repeat without `--check-only` after reviewing the
content-free receipt:

```bash
python3 <release-dir>/deploy/prepare-control-plane-activation.py \
  --release-dir <release-dir> \
  --env-file ~/.config/codex-control-plane/control-plane.env \
  --drop-in ~/.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf \
  --check-only
```

The helper updates only the declared source revision and expected package
fingerprint. It preserves unrelated settings, never prints credentials, and
does not change `current`, reload systemd, restart the service, alter admission
or touch SQLite. If the second file cannot be replaced, it restores the first
file and returns a failure instead of leaving the two identity sources split.

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
  durable central admission mode among `open`, `recovery`, and `scoped_pilot`.
  The last mode admits only the exact live service decision and allowed lanes;
  it is not a general reopening. Recovery blocks
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
  A later pilot may proceed past this unresolved action only for the same
  private-tunnel service principal and exact binding/workspace generation,
  when the durable records prove one bounded file-read intent, exactly one
  attempt, the same quarantined `unknown` receipt and evidence digest, and an
  empty local handle. Health and backup projections continue to count it as
  unresolved. Generic metadata actions, another principal/target, any receipt
  or intent drift, and unobserved dispatches still block a new pilot.
  A separate operator-only
  `POST /v1/action-dispositions/quarantine-historical-unobserved-dispatch`
  (and same-origin browser route) handles one narrower legacy case: an expired
  `workspace_context` action that is still `dispatch_unconfirmed`, has exactly
  one attempt and zero receipts, and whose node is stale/unavailable or lacks a
  valid local policy/runtime observation. It requires the literal declaration
  `HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH` plus a bounded rationale. The
  disposition is stored in a separate evidence table with an attempt-bound
  digest; it leaves the action `dispatch_unconfirmed`, creates no receipt,
  never retries and does not open admission. This is an explicit owner risk
  decision, not proof that the node did or did not read the workspace.
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

  The façade declares exactly the eight public `smart-v3` tool names. Only
  `workspace_context` currently has an explicit control-plane `context_id`
  envelope and implemented operations; the other seven names deliberately
  advertise an empty schema plus `capability_state=unavailable` and return the
  typed `LOCAL_ADMISSION_BRIDGE_REQUIRED` result. This is not a byte claim
  about the Windows tools' local input schemas and does not imply they can
  queue work. `workspace_context` defaults to
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
Schema migrations are additive, source-versioned (current `user_version=28`),
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

The optional `codex-control-plane-authority-renewal` service/timer keeps one
configured shared service grant and one exact scoped-pilot decision inside
their existing 30-day and 24-hour limits. It calls only the authenticated
operator renewal routes and does not store or print the MCP bearer. The timer
is intentionally disabled until `CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED=true`
and the protected environment names the accepted grant and decision. If the
target, binding, workspace generation, admission, or action reconciliation is
not current, renewal fails closed; it never reopens admission or silently
rebinds another Windows folder.
The oneshot schedule runs five minutes after timer activation, then 15 minutes
after each service completion. After installing or replacing the timer, confirm
`systemctl --user list-timers codex-control-plane-authority-renewal.timer` shows
a next elapse time; an enabled timer with no next elapse is not a running
renewal schedule.

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
enrolled node can then keep a long-lived authenticated connection. Its ordinary
`poll` mode is deliberately non-executing **and does not call the central
dequeue endpoint**; this prevents an unsupported client from allocating a
`dispatch_unconfirmed` attempt without a receipt. The packaged Supervisor uses
`run-connected-agent`: it sends heartbeat/reconnect independently of any
short-lived context or read-only policy, then polls only the standing local
capability lanes that the owner has installed (`file-read`, `approved-patch`,
`exec`, and bounded artifacts).

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
origin/device/endpoint **and** an exact current local workspace
ID/generation registry entry; on failure it does not heartbeat or dequeue. Each
iteration then publishes a fresh strict runtime heartbeat before the one
read-only poll. The process has no scheduler installer, cannot run longer than
24 hours, and must be started deliberately again after logout/reboot.

```powershell
# One hour at a 60-second cadence; do not run this before the explicit policy
# installation and Windows ACL gate above have been completed.
& '<installed>\resources\resources\control-plane\node-agent.cmd' run-read-only-loop `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json" `
  --interval-seconds 60 `
  --max-iterations 60
```

The loop prints only bounded lifecycle summaries. A degraded runtime or
transport error is recorded for that iteration and never authorizes a retry of
a possible local effect; an interrupted prepared bridge entry remains an
`unknown` receipt as with the one-shot lane.

### Long-lived same-user connected agent

After the packaged node has a node configuration, the named
`run-connected-agent` entrypoint is managed by the existing **same-user Recovery
Supervisor** in a newly installed candidate. The Supervisor verifies the
packaged Python and agent hashes from its manifest, then starts the agent as
soon as the credential-bearing node configuration is valid. This keeps an
authenticated heartbeat independent from effect authority: when the workspace
registry or standing file/patch/exec policy is absent, the agent runs in
heartbeat-only mode and every capability lane remains disabled by its own
fail-closed admission check. An older supervisor manifest has no agent fields
and remains `manifest_legacy`; it never guesses an agent path or starts one.

Every iteration sends an authenticated runtime heartbeat first, even when no
read-only policy exists. It then revalidates each installed standing policy
and exact local workspace generation before polling that lane. Missing or
disabled `file-read`, `approved-patch`, `exec`, or artifact authority is
reported as a disabled lane and skipped; it never broadens authority or
dequeues work for that lane. Runtime, transport, or authentication failures
use bounded exponential backoff and retry the heartbeat; a local journal and
the existing per-lane locks prevent duplicate effects. One atomically-created
connected-agent lock next to the private node configuration prevents two
same-profile connected agents from polling concurrently. A lock is reclaimed
only when its recorded PID is confirmed dead; malformed or uncertain locks
remain fail-closed for local operator review.

```powershell
# The packaged same-user Supervisor starts this exact command after enrollment.
# Running it manually is only for focused diagnostics. The command does not
# install another Scheduled Task and does not support logged-out Windows or
# Session 0/SYSTEM execution.
& '<installed>\resources\resources\control-plane\node-agent.cmd' run-connected-agent `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json" `
  --interval-seconds 15 `
  --max-backoff-seconds 300
```

`--max-iterations` is a focused diagnostic/test bound only; the default `0`
means the supervisor owns the process lifetime. The older
`run-read-only-agent` command remains available for explicit bounded pilot
diagnostics, but it is no longer the Supervisor's product path. Do not use the agent as proof
of central mutation, unattended boot, or a complete Windows onboarding flow:
those gates require the separate pairing, lifecycle and authority proof.

### Local workspace registration, capability replacement and retirement

Before Ubuntu can issue a usable binding, the same Windows user selects one
local root in Command Center and registers it. `read` is mandatory; `write`
and `exec` are explicit local capability choices and remain a local ceiling,
not an OS Administrator elevation or an Ubuntu per-command approval. The node
writes the canonical root only to its private `control-plane-workspaces.json`,
then sends Ubuntu only an opaque workspace ID, generation, display label and
capability inventory. Registration alone does not create a binding, context,
policy, grant or task authority.

Changing a label or capability is never an in-place overwrite. The owner must
confirm a separate `replace-workspace` operation. The agent persists a
phase-only journal, retires the old generation at Ubuntu, disables local
policies bound to that generation, registers a new generation with the same
workspace ID, and updates the private registry only after the new central
receipt is valid. A lost response or crash resumes the same phase; it does not
create a duplicate workspace. Existing bindings/tasks are fenced by the
central generation change and must be bound again.

Removing a root is also a local Command Center action. The UI lists only the
local display label and opaque identity; it sends the exact identity/generation
to Ubuntu for retirement. Ubuntu closes matching live contexts and settles only
actions that have not been dispatched. The node deletes its private registry
entry **only after** it receives the matching central retirement receipt. If
the response is lost, it keeps the entry and retries the same identity instead
of creating a new target or guessing that a remote effect completed.

For focused break-glass diagnostics only, the packaged agent supports the
following path-free operations. Do not substitute a manually chosen path for
an opaque identity during retirement.

```powershell
& '<installed>\resources\resources\control-plane\node-agent.cmd' list-workspaces `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json"

& '<installed>\resources\resources\control-plane\node-agent.cmd' replace-workspace `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json" `
  --workspace-path 'C:\path\to\same-root' `
  --display-name 'same-root' `
  --capability-read --capability-write --capability-exec `
  --confirm-replace

& '<installed>\resources\resources\control-plane\node-agent.cmd' retire-workspace `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json" `
  --workspace-id 'workspace_<registered-id>' `
  --workspace-generation 'generation_<registered-generation>'
```

### Legacy read-only policy assignment (compatibility only)

The earlier pilot asked an Ubuntu operator to issue a `ctx_…` value and made
the Windows user paste it into Command Center. That path is retired from the
normal trusted-workspace flow. The account OAuth and shared private-service
lanes are distinct; the latter does not identify individual Business members.
The intended sequence is authenticated connector → authorized target selection
→ Ubuntu creates one opaque `binding_id` for the
already-registered node/workspace generation → the node keeps standing
`file-read` and `approved-patch` policies locally. A separate structured
`exec` policy is not installed by Command Center in this candidate. Every
task pins the binding and the node reconnects after reboot
without a context copy or per-command approval. The public Windows path never
accepts or displays a context ID. An Operator Token, Tunnel credential, API
key, or context identifier is never a substitute for that account binding.

The packaged Command Center exposes workspace registration, capability changes,
credential rotation and binding status. The agent sends only opaque workspace
ID, generation and selected capability; the canonical path and credential stay
local to the node. It is not an auto-enrollment side effect, does not change
the Windows user's OS role, and does not create a global active workspace.
The launcher fixes bundled Python, installed Electron tree, packaged runtime
mode and `%APPDATA%\web-mcp-assistant`; it does not use a source checkout or
global Node. Do not copy a policy or credential between nodes.

The `install-read-only-policy-*` commands below remain for **legacy pilot and
compatibility evidence only**. They are not the final trusted-workspace
onboarding path, do not grant standing write/exec, and must not be described as
the normal daily approval flow. The standing profile is enabled only after its
separate OAuth scope, node-local policy and Windows package/live gates pass.

```powershell
# Run only on the logged-in Windows pilot node. The installed launcher supplies
# --runtime-mode packaged, --project-root and --node itself.
& '<installed>\resources\resources\control-plane\node-agent.cmd' install-read-only-policy-from-assignment `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json" `
  --workspace-id 'workspace_<registered-id>' `
  --workspace-generation 'generation_<registered-generation>' `
  --confirm-install

# Credential-free local observation, then an explicit local fail-closed stop.
& '<installed>\resources\resources\control-plane\node-agent.cmd' inspect-read-only-policy
& '<installed>\resources\resources\control-plane\node-agent.cmd' disable-read-only-policy --confirm-disable
```

The install command refuses a missing confirmation, absent/ambiguous/expired
internal assignment, a missing/changed/removed local workspace registration, an
over-24-hour policy, malformed server template, an already existing policy without
`--replace`, or a caller-supplied packaged data root. It returns only a policy
contract SHA, expiry, runtime mode and
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
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json" `
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
