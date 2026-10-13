import hashlib,hmac,json,os,re,sqlite3,stat,subprocess,time,urllib.request
from pathlib import Path
TASK="task_fd7cb4192b7144bebec0275e66d5eb95"; ACTION="act_65fa937277dd4963a5ca39ffe9e291ec"; UNKNOWN="rcpt_3c774da48ff34d34a342c824d8dc94b8"
DEVICE="4c4b7a5b-7744-49ae-a490-78a528a00471"; GENERATION="generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"; BINDING="bind_71661b1046884174b01c99af5f8546aa"; PRINCIPAL="svcprn_cd98750c7c7e45678d201066dc1b7d7a"; GRANT="mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"; EPOCH="activation-mv5cvpnu-2ddc4f6edfe0487ec46a1594cb87218d"; PROCESS="8vZ_MQ-kNrTus9ch"; SERVER="MSZYKc9xLwRhDOMM"
OUT=Path("/tmp/close-patch019-task.json")
def req(x,c):
 if not x: raise RuntimeError(c)
def service():
 pid=int(subprocess.check_output(["systemctl","--user","show","codex-control-plane.service","--property=MainPID","--value"],text=True))
 req(pid==970133,"SERVING_PID_CHANGED")
 env=dict(x.split("=",1) for x in Path(f"/proc/{pid}/environ").read_text().split(chr(0)) if "=" in x)
 req(env.get("CONTROL_PLANE_MCP_AUTH_MODE")=="private_tunnel_service" and env.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID")==PRINCIPAL and env.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID")==GRANT,"PRIVATE_SERVICE_CHANGED")
 db=Path(env["CONTROL_PLANE_DB"]).resolve(); c=sqlite3.connect(db.as_uri()+"?mode=ro",uri=True); c.row_factory=sqlite3.Row; c.execute("PRAGMA query_only=ON"); return pid,env,c
def census(c):
 a=dict(c.execute("SELECT delivery_state,settled_at_ms FROM actions WHERE action_id=?",(ACTION,)).fetchone()); t=dict(c.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?",(TASK,)).fetchone()); w=dict(c.execute("SELECT released_at_ms FROM mcp_task_writer_leases WHERE task_id=?",(TASK,)).fetchone()); rs=[dict(x) for x in c.execute("SELECT receipt_id,receipt_state,local_handle FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id",(ACTION,))]; n=dict(c.execute("SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms FROM nodes WHERE device_id=?",(DEVICE,)).fetchone()); return a,t,w,rs,n
def call(token,name,args):
 body={"jsonrpc":"2.0","id":args["operation"],"method":"tools/call","params":{"name":name,"arguments":args,"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}
 r=urllib.request.Request("http://127.0.0.1:8766/mcp",data=json.dumps(body).encode(),method="POST",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json","Accept":"application/json","MCP-Protocol-Version":"2026-07-28","Mcp-Method":"tools/call","Mcp-Name":name})
 with urllib.request.urlopen(r,timeout=10) as q: raw=q.read(196609)
 req(len(raw)<=196608,"MCP_RESPONSE_TOO_LARGE"); out=json.loads(raw); req("error" not in out and out.get("result",{}).get("isError") is not True,"MCP_CALL_REJECTED"); return out
pid,env,c=service(); a,t,w,rs,n=census(c)
req(a["delivery_state"]=="settled" and a["settled_at_ms"] is not None,"ACTION_NOT_SETTLED"); req(t["closed_at_ms"] is None and w["released_at_ms"] is None,"TASK_ALREADY_CLEANED"); req(len(rs)==2 and any(x["receipt_id"]==UNKNOWN and x["receipt_state"]=="unknown" for x in rs) and any(x["receipt_state"]=="failed" for x in rs),"TERMINAL_RECEIPT_SET_REQUIRED")
cred=Path.home()/".config/codex-control-plane/ubuntu-root-mcp-authorization"; info=cred.stat(); req(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_mode&0o77==0,"CREDENTIAL_NOT_PROTECTED"); token=cred.read_text().strip().removeprefix("Bearer "); req(re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}",token),"CREDENTIAL_INVALID")
g=c.execute("SELECT token_digest,principal_id,revoked_at_ms,expires_at_ms FROM mcp_service_grants WHERE grant_id=?",(GRANT,)).fetchone(); req(g and hmac.compare_digest(g["token_digest"],hashlib.sha256(b"coding-tools-control-plane:mcp-service-grant:v1\0"+token.encode()).hexdigest()) and g["principal_id"]==PRINCIPAL and g["revoked_at_ms"] is None and g["expires_at_ms"]>int(time.time()*1000)+60000,"SERVICE_GRANT_INVALID")
call(token,"task_control",{"operation":"writer_release","task_id":TASK,"reason":"r4_patch019_receipt_timeout_reconciled_terminal_failed"})
a,t,w,rs,n=census(c); req(w["released_at_ms"] is not None,"WRITER_NOT_RELEASED")
call(token,"workspace_context",{"operation":"task_close","task_id":TASK})
a,t,w,rs,n=census(c); req(t["closed_at_ms"] is not None and w["released_at_ms"] is not None and a["settled_at_ms"] is not None,"TASK_CLEANUP_NOT_VERIFIED"); req(len(rs)==2 and any(x["receipt_id"]==UNKNOWN for x in rs),"UNKNOWN_NOT_PRESERVED"); req(n["readiness"]=="ready" and n["runtime_instance_id"]==PROCESS and n["mcp_server_instance_id"]==SERVER and n["activation_epoch"]==EPOCH,"NODE_CHANGED_DURING_CLEANUP")
result={"operation":"close_r4_patch019_task","ok":True,"task_id":TASK,"action_id":ACTION,"task_closed_verified":True,"writer_released_verified":True,"unknown_receipt_preserved":True,"action_replayed":False,"terminal_receipt_state":"failed","observed_at_ms":int(time.time()*1000)}
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"operation":result["operation"],"ok":True,"task_closed_verified":True,"writer_released_verified":True,"unknown_receipt_preserved":True}))

