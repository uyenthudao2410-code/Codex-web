"""Read-only, redacted service and queue preflight. Run over SSH stdin."""
import hashlib
import json
import shlex
import sqlite3
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

home = Path('/home/svhome')
config = {}
for raw in (home / '.config/codex-control-plane/control-plane.env').read_text().splitlines():
    if not raw.strip() or raw.lstrip().startswith('#') or '=' not in raw:
        continue
    key, value = raw.split('=', 1)
    if key.strip() in {'CONTROL_PLANE_DB', 'CONTROL_PLANE_HEALTH_URL', 'CONTROL_PLANE_BIND', 'CONTROL_PLANE_PORT'}:
        parts = shlex.split(value, comments=True)
        if len(parts) == 1:
            config[key.strip()] = parts[0]
url = config.get('CONTROL_PLANE_HEALTH_URL') or 'http://' + config.get('CONTROL_PLANE_BIND', '127.0.0.1') + ':' + config.get('CONTROL_PLANE_PORT', '8765') + '/healthz'
parsed = urlsplit(url)
assert parsed.scheme in {'http', 'https'} and parsed.hostname and not parsed.username and not parsed.password and not parsed.query and parsed.path == '/healthz'
with urllib.request.urlopen(url, timeout=10) as response:
    health = json.load(response)
db = Path(config['CONTROL_PLANE_DB']).expanduser().resolve()
connection = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=5, isolation_level=None)
connection.row_factory = sqlite3.Row
connection.execute('PRAGMA query_only=ON')
connection.execute('BEGIN')
now = int(time.time() * 1000)
states = {r['delivery_state']: r['total'] for r in connection.execute('SELECT delivery_state, COUNT(*) AS total FROM actions GROUP BY delivery_state')}
quarantined = connection.execute("""SELECT COUNT(DISTINCT a.action_id) FROM actions a
  JOIN (SELECT action_id FROM action_reconciliations WHERE disposition='quarantined_unknown'
  UNION ALL SELECT action_id FROM action_dispatch_dispositions WHERE disposition='historical_read_only_unobserved_dispatch') q ON q.action_id=a.action_id
  WHERE a.delivery_state IN ('dispatch_unconfirmed','accepted','reconcile_required')""").fetchone()[0]
unresolved = sum(states.get(s, 0) for s in ('dispatch_unconfirmed', 'accepted', 'reconcile_required'))
queue = {
    'delivery_state_counts': states,
    'unresolved_action_count': unresolved,
    'quarantined_unresolved_action_count': quarantined,
    'unquarantined_unresolved_action_count': unresolved - quarantined,
    'queued_unexpired_count': connection.execute("SELECT COUNT(*) FROM actions WHERE delivery_state='queued' AND expires_at_ms>?", (now,)).fetchone()[0],
    'open_task_count': connection.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE closed_at_ms IS NULL AND expires_at_ms>?', (now,)).fetchone()[0],
    'active_writer_lease_count': connection.execute('SELECT COUNT(*) FROM mcp_task_writer_leases WHERE released_at_ms IS NULL AND expires_at_ms>?', (now,)).fetchone()[0],
    'live_pilot_count': connection.execute('SELECT COUNT(*) FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL AND expires_at_ms>?', (now,)).fetchone()[0],
    'admission_mode': connection.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0],
    'sqlite_integrity': connection.execute('PRAGMA integrity_check').fetchone()[0],
}
connection.execute('ROLLBACK')
connection.close()
current = (home / '.local/lib/codex-control-plane/current').resolve()
manifest = json.loads((current / 'release-manifest.json').read_text())
unit = subprocess.run(['systemctl', '--user', 'show', 'codex-control-plane.service', '-p', 'ActiveState', '-p', 'SubState', '-p', 'MainPID', '-p', 'NRestarts'], text=True, capture_output=True, check=True)
receipt = {
    'operation': 'redacted_read_only_server_preflight',
    'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'current_release': current.name,
    'manifest_identity': {k: manifest[k] for k in ('source_revision','package_source_sha256','control_plane_schema_version')},
    'web_ui_sha256': hashlib.sha256((current / 'control-plane/control_plane/web_ui.py').read_bytes()).hexdigest(),
    'service': dict(line.split('=', 1) for line in unit.stdout.splitlines()),
    'health_url': url,
    'health': {k: health.get(k) for k in ('ok','service','service_instance_id','package_source_sha256','expected_package_source_sha256','declared_source_revision','started_at_ms','schema_version','admission_mode','mcp_authentication_mode')},
    'queue': queue,
    'remote_mutation': False,
}
print(json.dumps(receipt, sort_keys=True, indent=2))
