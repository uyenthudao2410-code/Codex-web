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
python -m control_plane
```

The default listener is `127.0.0.1:8765`. Do not bind a public address until a
network and TLS/authentication boundary has been explicitly configured.

## Current API boundary

- `GET /healthz` is unauthenticated and reports only service/SQLite health.
- A node can post `/v1/enrollment-requests` with a hash of its locally-generated
  secret. The operator lists and approves that exact request; the secret never
  crosses the network or enters Git.
- `POST /v1/nodes/enroll` remains an operator-only bootstrap path; it returns a
  per-node credential once, which must be placed in protected configuration.
- `POST /v1/bindings`, `/v1/contexts`, `/v1/work-requests`, and `/v1/actions`
  require the operator bearer token.
- `POST /v1/nodes/{device_id}/heartbeat`, `/poll`, and `/receipts` require the
  node credential. Polling records `dispatch_unconfirmed` before returning an
  action; timeout/reconnect is reconciled using the same action/key.

This is not yet an MCP facade or a Windows local-MCP execution adapter. It is
safe to deploy for registry, durable intake and receipt/reconciliation testing;
mutation remains blocked until that adapter can pass the local authority gate.

## Node enrollment without copying a server secret

On the node, choose a private configuration path outside the repository and run
the client with the exact stable identities obtained from the local runtime:

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.node_agent request-enrollment `
  --config "$env:APPDATA/coding-tools-control-plane/node.json" `
  --server-url http://100.116.112.22:8765 `
  --device-id <installed-device-id> `
  --endpoint-id <current-endpoint-id> `
  --display-name <installed-display-name>
```

Approve the returned enrollment ID on the server under the operator token. The
agent can then send a heartbeat. Its `poll` mode is deliberately non-executing
until the local MCP admission adapter has been implemented and tested.

To publish the Hub's *actual*, fail-closed status after the Windows user has
logged in, use the one-shot adapter below. It reads `dev-ui-lifecycle.js
status`; it reports `ready` only when that command reports both
`components_ready=true` and `fully_ready=true`. A current process with connector
or admission pending is `degraded`, not ready.

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m control_plane.node_agent runtime-heartbeat `
  --config "$env:APPDATA/coding-tools-control-plane/node.json" `
  --project-root "$PWD"
```

This command does not execute a remote action and does not make Electron work
while Windows is logged out. It may later be called by a logon-scoped scheduler
only after the interactive-runtime availability design has its own proof.

## Focused proof

```powershell
$env:PYTHONPATH = "$PWD/control-plane"
python -m unittest discover -s control-plane/tests -v
```
