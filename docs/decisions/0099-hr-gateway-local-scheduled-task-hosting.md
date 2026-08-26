# 0099 HR Gateway Local Scheduled Task Hosting

Date: 2026-08-26

## Status

Accepted for local implementation and current-source activation verification only. This decision does not promote a production deployment, alter HR authorization, or change Finance authority.

## Context

C1-C through C4 hardening reached deterministic acceptance while the live HR Gateway on port 3001 still belonged to an older `dev:all` process tree. Restarting that mixed tree would also restart unrelated services and violate the hardening boundary. A detached shell child would not supply durable ownership, restart, or current-source evidence. Node also has no native Windows SCM service host in this repository.

## Decision

1. Add a Windows-only local provider `scripts/providers/hr-gateway-runtime-provider.ps1` managing exactly one Scheduled Task, `STA-HR-Gateway-Local`, and exactly one application port, 3001.
2. Run the task as the current Windows user with `Interactive` logon and `Limited` run level. Trigger at logon, allow start-on-demand, configure five bounded one-minute restart attempts, and set no task execution-time limit so the Gateway may remain long-running.
3. The task executes only `scripts/providers/hr-gateway-task-runner.ps1` from this checkout. The runner directly starts `node backend/server.js`, redirects stdout/stderr to `%LOCALAPPDATA%\STA\HR-Gateway`, and remains alive for the child lifetime.
4. Define current-source identity as a SHA-256 manifest over runtime-relevant backend JavaScript/JSON files. Exclude `node_modules`, tests, logs, certificates, coverage output, and `.env*`; no secret content or provider payload enters the receipt.
5. Write an atomic local receipt only after loopback `/health` is 2xx and the spawned Node PID owns port 3001. Bind the receipt to workspace, source fingerprint, gateway PID, PID creation time, health state, and local hosting mode.
6. `Status` is read-only and reports `ready=true` only when task configuration, receipt source fingerprint, live PID creation identity, listener PID, checkout ownership, and ready health receipt all agree.
7. `Ensure` is the activation/convergence command. It may stop only the current port-3001 listener after the listener/ancestor chain proves this checkout and the HR runtime role, then revalidates PID creation identity immediately before `taskkill /T /F`. It never kills an ancestor process.
8. If the listener is owned by `scripts/start-runtime.cjs`, fail closed as `HR_GATEWAY_MIXED_SUPERVISOR_ACTIVE` instead of fighting a supervisor that can recreate the child. Unknown/cross-checkout listeners fail closed as `HR_GATEWAY_PORT_IN_USE_UNOWNED`.
9. The provider contains no unrelated-service start/stop/prepare path. `Stop` and `Unregister` act only on the owned Scheduled Task and a receipt-bound Gateway listener.
10. This is a local workstation hosting mechanism. Production process management, log shipping, alerting, multi-replica session uniqueness, tenant UAT, soak, and SLO claims remain separately governed.

## Alternatives Considered

1. Restart `dev:all`: rejected because it couples HR activation to unrelated service interruption.
2. Kill the mixed root supervisor: rejected because the parent owns unrelated runtime children.
3. Launch `node server.js` detached from the current shell: rejected because lifetime and source ownership would remain unverifiable.
4. Register Node directly with Windows SCM: rejected because this repository has no Node service wrapper and SCM expects service-control semantics.
5. Use a current-user Scheduled Task: accepted because it provides an OS-owned local lifecycle without elevation or cross-service coupling and can retain a long-running wrapper that emits a verifiable receipt.

## Consequences

Positive:

- HR Gateway current-source activation no longer requires restarting sibling services.
- The operating state is machine-readable and bound to source identity, PID creation identity, listener ownership, and health.
- A terminal or MCP command ending does not terminate the Gateway.
- Re-running `Ensure` is convergent when the source and live receipt already match.

Tradeoffs:

- The task is local and current-user scoped; it is not a production service manager.
- Logoff ends the interactive task; the at-logon trigger restores it on the next login.
- A live mixed `npm start` supervisor intentionally blocks takeover because safe HR-only ownership cannot be established while that supervisor can restart the child.

## Validation

- `npm run test:hr-gateway-runtime-provider`
- `node scripts/test-start-all-runtime.cjs`
- `node --test scripts/test-runtime-preflight-cleanup.cjs`
- Live `hr:gateway:runtime:ensure` followed by repeated `Status` receipts.
- Live evidence must show the new 3001 PID is receipt-bound/current-source and unrelated sibling runtime PIDs are unchanged across activation.

## Follow-Up

- Production service manager selection and operational monitoring remain separate work.
- If local all-service startup is later redesigned, teach it to detect the HR Scheduled Task instead of creating a competing port-3001 child.
