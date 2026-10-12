# Control-plane release deployment

This archive contains **codex-control-plane-70de202d93c9a759befe5d38491ce54e9ef4b3cd**. It is a source artifact, not an
activated service. It contains no SQLite database, operator token, node
credential, session, backup, or private environment file.

## Prepare outside the release tree

1. Inspect `release-manifest.json`; verify the selected Git revision, package
   fingerprint and each file digest before extracting it under a versioned path
   such as `~/.local/lib/codex-control-plane/releases/<revision>`.
2. Copy `deploy/control-plane.env.example` to
   `~/.config/codex-control-plane/control-plane.env`, replace every placeholder,
   and set mode `0600`. Keep the database and backups in an owner-only state
   directory outside `releases/`.
   For the optional root MCP Tunnel, copy
   `deploy/control-plane-mcp-tunnel.env.example` separately to
   `~/.config/codex-control-plane/mcp-tunnel.env` with mode `0600`. Its unit must
   not load `control-plane.env`. Keep the scoped MCP Authorization header in
   its own owner-private regular file, and store the OpenAI Runtime API Key as
   a file reference in the protected tunnel-client profile.
3. Run `python3 deploy/control-plane-verify-release.py --release-dir <release>`
   and compare its content-free receipt to this manifest. Before switching
   `current`, prepare the two protected release identity files together with
   `python3 deploy/prepare-control-plane-activation.py --release-dir <release>
   --env-file <control-plane.env> --drop-in <10-immutable-release.conf>
   --check-only`, then repeat without `--check-only` after reviewing the
   receipt. This helper does not restart anything. Install the eight
   unit/timer examples from `deploy/` as user units (the authority-renewal
   pair is optional and must remain disabled until its protected IDs are
   populated). They only
   execute `~/.local/lib/codex-control-plane/current/deploy/...`; `current` must
   be an operator-controlled symlink to exactly one verified release directory.

## Controlled activation

Before changing `current`, close admission through the existing authenticated
control-plane procedure, inspect active/inflight work, and make a verified
backup. A schema migration is allowed only after that verified snapshot and is
part of starting the selected service; never rewrite a live database from the
archive or use an application rollback as a database rollback. Point `current`
at the selected release, refresh units, then start or
restart only the named control-plane service through the supported systemd
procedure. Verify `/healthz` with the package fingerprint in this manifest
before reopening admission. Do not infer a live deployment from archive creation
or a matching source checkout.

## Rollback

Close admission, fence/reconcile any in-flight work, point `current` at the
previous compatible verified release, and obtain new process/health identity
evidence before an explicit reopen. Database restore is a separate recovery
decision: never copy a database into a release directory or restore it merely
because an application binary was rolled back.
