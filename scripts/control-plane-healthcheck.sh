#!/usr/bin/env bash
# Check the live control-plane process and the freshness of its last verified
# automatic backup. It is observation-only: a failure is left for an operator
# or systemd journal consumer; this script never restarts a service or node.
set -euo pipefail

umask 077

readonly PROJECT_ROOT='/home/svhome/DEV/Codex-web'
readonly STATE_DIR='/home/svhome/.local/state/codex-control-plane'
readonly BACKUP_DIR="$STATE_DIR/backups"
readonly BACKUP_STATUS="$BACKUP_DIR/last-automatic-backup.json"
readonly HEALTH_STATUS="$BACKUP_DIR/last-healthcheck.json"
readonly HEALTH_URL='http://100.116.112.22:8765/healthz'
readonly MAX_BACKUP_AGE_SECONDS=8100 # two hourly periods plus scheduler jitter

install -d -m 700 "$BACKUP_DIR"
exec 9>"$BACKUP_DIR/.healthcheck.lock"
if ! flock -n 9; then
  printf 'control-plane healthcheck is already running\n' >&2
  exit 3
fi

package_receipt=$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/control-plane" \
  /usr/bin/python3 -B -m control_plane.maintenance package-fingerprint)
package_sha256=$(printf '%s' "$package_receipt" | /usr/bin/python3 -c \
  'import json, sys; print(json.load(sys.stdin)["package_source_sha256"])')

# Keep admission=open as an actionable pilot-readiness condition. An authorized
# recovery mode will therefore remain observable but make this check fail until
# the owner has reconciled and explicitly re-opened admission.
deployment_receipt=$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/control-plane" \
  /usr/bin/python3 -B -m control_plane.deployment_verifier \
  --health-url "$HEALTH_URL" \
  --expected-package-source-sha256 "$package_sha256" \
  --expected-admission open)

status_tmp="$BACKUP_DIR/.last-healthcheck.$$.json"
/usr/bin/python3 - "$status_tmp" "$BACKUP_STATUS" "$deployment_receipt" "$MAX_BACKUP_AGE_SECONDS" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

target, backup_path, deployment_text, max_age_text = sys.argv[1:]
backup = json.loads(Path(backup_path).read_text(encoding="utf-8"))
captured_at = datetime.fromisoformat(backup["captured_at_utc"].replace("Z", "+00:00"))
age_seconds = (datetime.now(timezone.utc) - captured_at).total_seconds()
max_age_seconds = int(max_age_text)
inspection = backup.get("inspection", {})
if (
    age_seconds < 0
    or age_seconds > max_age_seconds
    or inspection.get("sqlite_integrity") != "ok"
    # Historic unknown read-only actions may have an explicit audited
    # quarantine. They remain counted as unresolved evidence, but only an
    # *unquarantined* delivery ambiguity keeps backup health red.
    or inspection.get("unquarantined_unresolved_action_count") != 0
):
    raise SystemExit("control-plane automatic backup is stale or not restorable")
deployment = json.loads(deployment_text)
Path(target).write_text(json.dumps({
    "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "backup_age_seconds": round(age_seconds, 3),
    "max_backup_age_seconds": max_age_seconds,
    "backup_snapshot_sha256": backup["snapshot"]["snapshot_sha256"],
    "deployment": deployment,
}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY
chmod 600 "$status_tmp"
mv -f "$status_tmp" "$HEALTH_STATUS"
printf '%s\n' "$deployment_receipt"
