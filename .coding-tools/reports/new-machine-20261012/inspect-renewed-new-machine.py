"""Read-only sanitized census after the authorized exact renewal."""
import datetime
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time
import urllib.request

DEVICE='4c4b7a5b-7744-49ae-a490-78a528a00471'
PILOT='pilot_dfb3174078d842299c41c6638830e505'
EPOCH='activation-mv4od6fe-c45648f5d945ceeb7f3640048b0e91b7'
EXPIRY=1791847531435
PACKAGE_SHA='sha256:f235d3a2898ad53597e3b48e55e27d2278ea7d6d0c9fb2fef21301467a5d9712'

def require(condition,code):
    if not condition: raise RuntimeError(code)

pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True).strip())
require(pid==912047,'MAIN_SERVICE_PID_CHANGED')
serving=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
db=Path(serving['CONTROL_PLANE_DB'])
con=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
con.execute('PRAGMA query_only=ON');con.row_factory=sqlite3.Row
now=int(time.time()*1000)
pilot=dict(con.execute('SELECT decision_id,binding_id,device_id,workspace_id,workspace_generation,principal_id,expires_at_ms,revoked_at_ms FROM scoped_pilot_decisions WHERE decision_id=?',(PILOT,)).fetchone())
node=dict(con.execute('SELECT readiness,last_seen_at_ms,activation_epoch,policy_state,policy_expires_at_ms FROM nodes WHERE device_id=?',(DEVICE,)).fetchone())
require(pilot['expires_at_ms']==EXPIRY and pilot['revoked_at_ms'] is None and EXPIRY>now,'EXACT_RENEWED_PILOT_CHANGED')
require(node['readiness']=='ready' and node['activation_epoch']==EPOCH and now-node['last_seen_at_ms']<90000
        and node['policy_state']=='enabled' and node['policy_expires_at_ms']>now,'EXACT_R4_READY_NOT_CURRENT')
open_tasks=con.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE device_id=? AND closed_at_ms IS NULL',(DEVICE,)).fetchone()[0]
writers=con.execute('SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.device_id=? AND l.released_at_ms IS NULL',(DEVICE,)).fetchone()[0]
require(open_tasks==0 and writers==0,'NEW_MACHINE_NOT_IDLE')
admission=con.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0]
require(admission=='scoped_pilot','ADMISSION_MODE_CHANGED')
timer={key:subprocess.check_output(['systemctl','--user','show','codex-control-plane-authority-renewal.timer','--property='+key,'--value'],text=True).strip()
       for key in ('ActiveState','UnitFileState','Persistent','Unit')}
require(timer['ActiveState']=='active' and timer['UnitFileState']=='enabled' and timer['Persistent']=='yes','RENEWAL_TIMER_NOT_ACTIVE')
renewal={key:subprocess.check_output(['systemctl','--user','show','codex-control-plane-authority-renewal.service','--property='+key,'--value'],text=True).strip()
         for key in ('MainPID','Result','ExecMainStatus')}
require(renewal=={'MainPID':'0','Result':'success','ExecMainStatus':'0'},'RENEWAL_ONESHOT_NOT_SUCCESSFUL_IDLE')
with urllib.request.urlopen('https://svhome.tail0e4032.ts.net/healthz',timeout=5) as response:
    health=json.loads(response.read(65536))
require(health.get('package_source_sha256')==PACKAGE_SHA and health.get('expected_package_source_sha256')==PACKAGE_SHA,'HTTPS_PACKAGE_HEALTH_NOT_EXACT')
con.close()
expiry=datetime.datetime.fromtimestamp(EXPIRY/1000,datetime.timezone.utc)
print(json.dumps({'operation':'renewed_new_machine_readonly_census','ok':True,'observed_at_ms':now,
                  'expires_at_utc':expiry.isoformat(timespec='milliseconds'),
                  'expires_at_utc_plus_07':expiry.astimezone(datetime.timezone(datetime.timedelta(hours=7))).isoformat(timespec='milliseconds'),
                  'pilot':pilot,'node':node,'heartbeat_age_ms':now-node['last_seen_at_ms'],'admission_mode':admission,
                  'open_tasks':open_tasks,'unreleased_writers':writers,'main_service_pid':pid,
                  'timer':timer,'renewal_oneshot':renewal,'https_health_ok':True,'serving_package_sha256':PACKAGE_SHA},separators=(',',':')))
