# Security Policy

Tools-Codex-web is a local Windows desktop execution bridge that lets authenticated AI clients operate a configured coding workspace through MCP. The current security boundary is the **Electron Execution Hub + Recovery Host + one Coding Tools MCP Runtime**. WebCodex server/runner security documents still apply inside that core subsystem, but they do not replace the Desktop boundary described here.

## Supported version

The current desktop package is `web-mcp-assistant 0.3.4`. Security fixes should target the currently maintained `0.3.x` line unless a release note states otherwise.

## Trust and authority model

- ChatWeb/ChatGPT and Codex Desktop are clients of the same Execution Hub truth; they must not create two peer Coding Tools runtimes that independently mutate the same workspace/ledger.
- Recovery Host owns primary service lifecycle. Electron is the UI/configuration client and Execution Control Center.
- Coding Tools MCP owns workspace mutation, deterministic proof, EOCL state, durable orchestration evidence, and write fencing.
- Semantic controller authority and repository write lease are separate. Controller transfer does not silently grant mutation rights.
- Codex App Server and OpenCode are secondary candidate/review/provider lanes. Provider availability, telemetry, or route selection does not grant independent authoritative write access to the primary checkout.
- `execution_route=auto` is currently fail-closed to deterministic while representative accepted paired evidence is insufficient.

## Workspace and command boundary

Coding Tools MCP enforces a configured workspace plus explicitly authorized roots. Relevant controls include path normalization, traversal/symlink escape protection, command policy, bounded output/session handling, runtime-specific HOME/TMP/CACHE, and secret-environment filtering according to permission mode.

Permission modes are `safe`, `trusted`, or `dangerous`. `dangerous` deliberately bypasses important safety gates and should be used only for a trusted local workspace when the operator understands the consequences. A host that does not support interactive permission elicitation does **not** create an implicit grant; `request_permissions` remains fail-closed.

## One Runtime, multiple clients

Codex Desktop should connect through the Electron-generated thin stdio proxy/loopback gateway rather than spawning a second Coding Tools MCP authority for the same workspace. The real MCP bearer remains owned by Electron/SecretStore; copied proxy configuration must not expose it.

## Recovery plane

The current source implements an independent break-glass Recovery MCP and, when configured, a separate Recovery Tunnel. It must not reuse the primary Coding Tunnel identity. Recovery is intentionally bounded: no arbitrary remote shell/process/RPC input; repair requires confirmation and forwards fixed authenticated recovery behavior; status/log projections remain secret-free.

## Runtime activation and restart

Do not kill the active MCP process from inside the request it is serving. `task_control(action="restart_runtime")` uses the supervised restart path and explicit confirmation. Source changes do not prove that the live process loaded them; verify the new process/runtime identity and revision/contract after runtime-affecting work.

## Secrets and logs

Never commit or expose MCP/tunnel/recovery/loopback tokens, OAuth/account credentials, private keys, secret-store exports, `.env` values, Authorization headers, or raw sensitive provider/workspace content. Provider usage/cost telemetry should persist measured numeric facts and correlation identifiers rather than prompt/response content.

## Durable orchestration evidence

`.coding-tools/orchestration/ledger.sqlite3` is the canonical local causal audit source for runs, waves, authority, delegations, proof lineage, observations and acceptance. Host-turn correlation should remain content-free (`turn_id`, `trace_id`, `span_id`) rather than persisting full ChatGPT prompts/responses.

## LSP and provider boundaries

Native LSP integration is a read-only semantic acceleration path; typed requests stay project-bound and constrained profiles must not become arbitrary JSON-RPC passthrough, execute repo code, fetch dependencies, or leak external paths. Resource pressure policy must be bounded/observable rather than hardcoded from one historical working-set sample.

OpenCode/Codex provider lanes remain bounded by source authority/traffic policy. Automatic provider routing is currently evidence-gated/off. Do not present internal estimated credits as provider billing.

## Git, release and destructive operations

Do not reset, clean, rebase, force-push, move published tags, overwrite releases, deploy, restart services, or mutate external systems unless explicitly authorized. Preserve unrelated dirty work and review intentional runtime evidence for sensitive content before publication.

## Reporting vulnerabilities

For vulnerabilities in this customized repository, contact the current repository owner/maintainer through GitHub using a private channel when sensitive details are involved. Use a public issue only for non-sensitive, minimized reproduction information. Report to upstream WebCodex only when the vulnerability actually belongs to that upstream/core component.

## Known boundary

This project is intended for controlled local/self-hosted operation. It is not a substitute for OS least privilege, endpoint protection, Git review, secret scanning, provider account controls, or production change-management policy.
