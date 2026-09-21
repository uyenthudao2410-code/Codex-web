#!/usr/bin/env bash
# Observe the selected release and backup freshness. A failure remains visible
# in the systemd journal; this script never restarts a service or node.
set -euo pipefail

umask 077

readonly RELEASE_ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly PACKAGE_ROOT="$RELEASE_ROOT/control-plane"
readonly BACKUP_DIR="${CONTROL_PLANE_BACKUP_DIR:-}"
readonly BACKUP_STATUS="$BACKUP_DIR/last-automatic-backup.json"
readonly HEALTH_STATUS="$BACKUP_DIR/last-healthcheck.json"
readonly HEALTH_URL="${CONTROL_PLANE_HEALTH_URL:-}"
readonly EXPECTED_ADMISSION="${CONTROL_PLANE_HEALTH_EXPECTED_ADMISSION:-}"
readonly MAX_BACKUP_AGE_SECONDS=8100 # two hourly periods plus scheduler jitter

if [[ ! -f "$PACKAGE_ROOT/control_plane/deployment_verifier.py" ]]; then
  printf 'control-plane release package is incomplete\n' >&2
  exit 2
fi
if [[ "$BACKUP_DIR" != /* || -z "$HEALTH_URL" ]]; then
  printf 'control-plane healthcheck requires CONTROL_PLANE_BACKUP_DIR and CONTROL_PLANE_HEALTH_URL\n' >&2
  exit 2
fi
if [[ "$EXPECTED_ADMISSION" != "open" && "$EXPECTED_ADMISSION" != "recovery" ]]; then
  printf 'control-plane healthcheck requires CONTROL_PLANE_HEALTH_EXPECTED_ADMISSION=open|recovery\n' >&2
  exit 2
fi

install -d -m 700 "$BACKUP_DIR"
exec 9>"$BACKUP_DIR/.healthcheck.lock"
if ! flock -n 9; then
  printf 'control-plane healthcheck is already running\n' >&2
  exit 3
fi

package_receipt=$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PACKAGE_ROOT" \
  /usr/bin/python3 -B -m control_plane.maintenance package-fingerprint)
package_sha256=$(printf '%s' "$package_receipt" | /usr/bin/python3 -c \
  'import json, sys; print(json.load(sys.stdin)["package_source_sha256"])')

deployment_receipt=$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PACKAGE_ROOT" \
  /usr/bin/python3 -B -m control_plane.deployment_verifier \
  --health-url "$HEALTH_URL" \
  --expected-package-source-sha256 "$package_sha256" \
  --expected-admission "$EXPECTED_ADMISSION")

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
