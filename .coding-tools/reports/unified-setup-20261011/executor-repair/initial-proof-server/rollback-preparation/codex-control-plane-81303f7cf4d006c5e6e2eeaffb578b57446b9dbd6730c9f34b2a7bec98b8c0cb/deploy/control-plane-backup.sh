#!/usr/bin/env bash
# Create a verified SQLite snapshot from the state directory selected in the
# protected systemd environment. This script never switches releases, changes
# admission, starts/stops a service, or contacts a node.
set -euo pipefail

umask 077

readonly RELEASE_ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly PACKAGE_ROOT="$RELEASE_ROOT/control-plane"
readonly SOURCE_DB="${CONTROL_PLANE_DB:-}"
readonly BACKUP_DIR="${CONTROL_PLANE_BACKUP_DIR:-}"
readonly STATUS_FILE="$BACKUP_DIR/last-automatic-backup.json"
readonly MIN_FREE_KIB=5242880 # 5 GiB
readonly RETAIN_DAYS=30

if [[ ! -f "$PACKAGE_ROOT/control_plane/maintenance.py" ]]; then
  printf 'control-plane release package is incomplete\n' >&2
  exit 2
fi
if [[ "$SOURCE_DB" != /* || "$BACKUP_DIR" != /* ]]; then
  printf 'control-plane backup requires absolute CONTROL_PLANE_DB and CONTROL_PLANE_BACKUP_DIR\n' >&2
  exit 2
fi
if [[ ! -f "$SOURCE_DB" ]]; then
  printf 'control-plane backup source is missing\n' >&2
  exit 2
fi

install -d -m 700 "$BACKUP_DIR"
exec 9>"$BACKUP_DIR/.automatic-backup.lock"
if ! flock -n 9; then
  printf 'control-plane backup is already running\n' >&2
  exit 3
fi

available_kib=$(df -Pk "$(dirname -- "$SOURCE_DB")" | awk 'NR == 2 { print $4 }')
if [[ ! "$available_kib" =~ ^[0-9]+$ ]] || (( available_kib < MIN_FREE_KIB )); then
  printf 'control-plane backup has insufficient free space\n' >&2
  exit 4
fi

captured_at=$(date -u +%Y%m%dT%H%M%SZ)
snapshot="$BACKUP_DIR/control-plane-automatic-$captured_at.sqlite3"
snapshot_receipt="$BACKUP_DIR/control-plane-automatic-$captured_at.snapshot.json"
inspection_receipt="$BACKUP_DIR/control-plane-automatic-$captured_at.inspection.json"

snapshot_result=$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PACKAGE_ROOT" \
  /usr/bin/python3 -B -m control_plane.maintenance snapshot \
  --source "$SOURCE_DB" --destination "$snapshot")
printf '%s\n' "$snapshot_result" > "$snapshot_receipt"

snapshot_sha256=$(printf '%s' "$snapshot_result" | /usr/bin/python3 -c \
  'import json, sys; print(json.load(sys.stdin)["snapshot_sha256"])')
inspection_result=$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PACKAGE_ROOT" \
  /usr/bin/python3 -B -m control_plane.maintenance inspect-snapshot \
  --source "$snapshot" --expected-sha256 "$snapshot_sha256")
printf '%s\n' "$inspection_result" > "$inspection_receipt"

status_tmp="$BACKUP_DIR/.last-automatic-backup.$$.json"
/usr/bin/python3 - "$status_tmp" "$snapshot_result" "$inspection_result" "$available_kib" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

target, snapshot_text, inspection_text, available_kib = sys.argv[1:]
snapshot = json.loads(snapshot_text)
inspection = json.loads(inspection_text)
Path(target).write_text(json.dumps({
    "captured_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "free_kib_before": int(available_kib),
    "snapshot": snapshot,
    "inspection": inspection,
}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY
chmod 600 "$snapshot" "$snapshot_receipt" "$inspection_receipt" "$status_tmp"
mv -f "$status_tmp" "$STATUS_FILE"

# This job owns only its exact automatic-snapshot filenames. It never prunes
# manual, pre-migration, recovery-candidate, or repository evidence files.
while IFS= read -r -d '' expired_snapshot; do
  expired_base="${expired_snapshot%.sqlite3}"
  rm -f -- "$expired_snapshot" "${expired_base}.snapshot.json" "${expired_base}.inspection.json"
done < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'control-plane-automatic-????????T??????Z.sqlite3' -mtime +"$RETAIN_DAYS" -print0)

printf '%s\n' "$inspection_result"
