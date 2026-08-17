# P1 Release Boundary Status

> Status: **blocked on execution infrastructure; gate definition is ready**
>
> Product source under acceptance: `3a3abaff72a8e6382e4c362865becba069e4ecfc`
>
> GitHub P1 gate definition: `.github/workflows/p1-release.yml`

## P1 scope

P1 covers the Windows Desktop Execution Hub / Coding Tools MCP / Recovery boundary. It does **not** require the Unix-only WebCodex Server to compile natively on Windows.

The P1 gate requires:

- exact clean checkout identity;
- locked Desktop and Coding Tools MCP dependencies;
- production dependency audit;
- Coding Tools MCP contract/tests;
- Desktop source tests;
- Recovery Host real-process fault matrix;
- Recovery Supervisor Windows logon registration in source mode;
- exact-source Windows NSIS packaging, including packaged-resource sanitation;
- Recovery Supervisor registration against the actual `dist/win-unpacked` executable in `packaged` mode;
- packaged executable identity/hash and fixed `--recovery-host` argv verification;
- installer and packaged-executable SHA-256 provenance;
- explicit rollback guidance retained with the release proof.

## Evidence already obtained on the new Windows machine

A detached clean linked worktree was created at exact product source `3a3abaff72a8e6382e4c362865becba069e4ecfc`, preserving unrelated WIP in the authoritative checkout.

The following gates passed on that clean worktree:

- `npm ci --offline` from `package-lock.json`;
- `npm test`;
- `npm run test:recovery:e2e`;
- Recovery Supervisor install/status/uninstall with a verified `MSFT_TaskLogonTrigger`.

These are supplementary local proofs. They do not replace the final P1 artifact/provenance gate.

## Current blockers

### GitHub hosted Actions

GitHub currently rejects hosted-runner jobs before checkout with:

> The job was not started because recent account payments have failed or your spending limit needs to be increased.

The P1 workflow therefore cannot yet produce the canonical `p1-release-proof-<sha>` artifact on GitHub.

### Local Coding Tools MCP execution ownership

On the new machine, task/run ownership projections can diverge across Coding Tools MCP execution instances: `task_control` can report an active P1 task while `agent_workflow` reports `TASK_STOPPED`, and a direct HEAVY packaging command is correctly rejected with `EXECUTION_OWNERSHIP_REQUIRED` because no consistent current RUN/WAVE owner is visible.

Do not bypass this fence. Packaging proof must be rerun only after one execution instance consistently owns the P1 RUN/WAVE.

## Completion rule

P1 is complete only when the corrected P1 gate finishes successfully for the accepted source, produces the NSIS installer plus `p1-release-provenance.json` and `P1-ROLLBACK.txt`, and the proof is retained on GitHub. Until then, keep P1 open.
