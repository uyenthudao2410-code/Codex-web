# Sandbox cached-session repair — source checkpoint

Observed root: E:/DEV/Codex-web, main @ 7999c4151cb501db86f2e4d0a2275d33fc248324; prior dirty changes preserved.

- Actual ChatGPT create/read/readback passed; original node --version Job exited 1 once and its task is closed. No original action was replayed.
- Read-only log classification: owned VM disappearance was confirmed at UTC 05:12:49, before command UTC 05:14:31. Runtime and epoch stayed r5b. The trigger for VM disappearance is unknown.
- Adapter now reconciles start for the exact cached ID before creating the next command request. Only exact structured already_started is accepted; guest-ready/protocol execution guards remain in force. Failed restart cleans the exact ID and unconfirmed cleanup blocks subsequent commands.
- Focused adapter validation: 30 tests and 12 subtests passed. First run had one old expectation of no warm lifecycle call; the expectation was updated to the new pre-command reconciliation and the successful result supersedes it.
- Native prior-daemon identity guard is being prepared because existing orphan reclaim proves process ownership but did not bind the prior sandbox ID to the requested ID.
- No new package activated, server changed, command dispatched or commit/push/release performed in this wave.

Next: finish native same-ID guard and validation/build, verify/activate r6, then cold/warm/stopped-session shared MCP command proof with exact one-attempt lineage and supported task cleanup.
