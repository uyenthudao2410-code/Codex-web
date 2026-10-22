# Exact Ubuntu local metadata activation

Copy the entire contents of `activate-exact-ubuntu-local-metadata.sh` and paste into the existing `svhome` Ubuntu shell. It needs no file transfer, download or key entry. Do not use sudo.

The script accepts only the confirmed baseline release, PID 970133, node hash e368fd239446c8313c871dd41e4b35356e40bef83fff0bff80debff528f92f96 and schema 29. It prepares a separate immutable release with exactly two inserted runtime lines and updated manifest identity.

It checks idle/causal state, pauses and restores competing timers, makes a verified database/config backup, uses the installed activation helper, switches current, and stops/starts only codex-control-plane.service. Pilots, grants, admission, tunnel service and credentials are preserved. No recovery admission API is called.

Success is JSON with `ok: true`, `stage: complete`, the new PID, package fingerprint, `pilots_and_admission_unchanged: true` and backup directory. A service/package/schema/busy/config mismatch aborts; do not replace the pinned values to bypass it.

If candidate start was attempted and postflight failed, the script leaves the candidate for review and never automatically stops or rolls it back. Preserve the returned error and inspect exact service identity before retrying.

This is a single purpose content derived overlay, not a Git release or proof of Windows command execution. Ubuntu deployment has not been performed from this Codex session.

The exact two user-observed generated caches `control-plane/control_plane/__pycache__/__init__.cpython-314.pyc` and `store.cpython-314.pyc` are allowed only during validation of this pinned live baseline. They remain untouched in that baseline and are excluded from the new candidate. Every manifested file is checked byte for byte; any third extra file is denied, and the complete candidate must pass the unchanged maintained verifier.

The pinned baseline health endpoint has no `service_pid` field. Process identity is proven through Linux TCP LISTEN socket inodes held by the exact systemd MainPID for both configured listeners, together with package and process-environment checks.
