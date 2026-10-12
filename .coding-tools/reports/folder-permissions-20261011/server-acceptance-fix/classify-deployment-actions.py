"""Capture content-free, read-only delivery/fence metadata from the target."""

import json
from pathlib import Path
import subprocess


REMOTE = r"""
import hashlib,json,pathlib,shlex,sqlite3,time
values={}
for line in pathlib.Path('/home/svhome/.config/codex-control-plane/control-plane.env').read_text().splitlines():
 if line.strip() and not line.lstrip().startswith('#'):
  key,raw=line.split('=',1); parts=shlex.split(raw,comments=True); values[key.strip()]=parts[0] if parts else ''
now=int(time.time()*1000)
with sqlite3.connect(pathlib.Path(values['CONTROL_PLANE_DB']).as_uri()+'?mode=ro',uri=True) as c:
 c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
 rows=c.execute('''SELECT a.action_id,a.owner_id,a.tool_name,a.delivery_state,a.device_id,a.workspace_id,a.workspace_generation,a.created_at_ms,a.expires_at_ms,a.settled_at_ms,a.arguments_json,a.request_id,a.context_id,a.binding_id,b.revoked_at_ms AS binding_revoked_at_ms,ctx.expires_at_ms AS context_expires_at_ms,ctx.closed_at_ms AS context_closed_at_ms,w.canceled_at_ms AS request_canceled_at_ms,r.disposition AS reconciliation_disposition,r.evidence_digest AS reconciliation_evidence_digest,d.disposition AS dispatch_disposition,d.evidence_digest AS dispatch_evidence_digest,tl.task_id FROM actions a JOIN bindings b ON b.binding_id=a.binding_id JOIN contexts ctx ON ctx.context_id=a.context_id JOIN work_requests w ON w.request_id=a.request_id LEFT JOIN action_reconciliations r ON r.action_id=a.action_id LEFT JOIN action_dispatch_dispositions d ON d.action_id=a.action_id LEFT JOIN mcp_task_action_links tl ON tl.action_id=a.action_id WHERE a.delivery_state!='settled' ORDER BY a.action_id''').fetchall()
 result=[]
 for row in rows:
  record=dict(row);arguments=json.loads(record.pop('arguments_json'));record['payload_operation']=arguments.get('operation')
  record['receipt_states']=[r[0] for r in c.execute('SELECT receipt_state FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id',(record['action_id'],))]
  record['attempt_count']=c.execute('SELECT COUNT(*) FROM delivery_attempts WHERE action_id=?',(record['action_id'],)).fetchone()[0]
  record['context_state']='closed' if record['context_closed_at_ms'] is not None else 'expired' if record['context_expires_at_ms']<=now else 'open'
  record['action_expired']=record['expires_at_ms']<=now
  result.append(record)
 fenced=[r for r in result if r['reconciliation_disposition']=='quarantined_unknown' or r['dispatch_disposition']=='historical_read_only_unobserved_dispatch']
 encoded=json.dumps(fenced,sort_keys=True,separators=(',',':')).encode()
 print(json.dumps({'observed_at_ms':now,'records':result,'fenced_count':len(fenced),'fenced_record_sha256':hashlib.sha256(encoded).hexdigest()},sort_keys=True))
"""
response = subprocess.run(
    ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'svhome@100.116.112.22', 'python3', '-'],
    input=REMOTE.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True,
)
value = json.loads(response.stdout)
output = Path(__file__).with_name('deployment-action-classification.json')
output.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'record_count':len(value['records']),'fenced_count':value['fenced_count'],
                  'fenced_record_sha256':value['fenced_record_sha256'],
                  'unfenced_records':[r for r in value['records'] if r['reconciliation_disposition'] is None and r['dispatch_disposition'] is None]},sort_keys=True))
