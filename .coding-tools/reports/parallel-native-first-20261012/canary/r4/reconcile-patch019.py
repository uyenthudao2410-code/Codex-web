import argparse,hashlib,importlib.util,json,os,sqlite3,subprocess,time
from pathlib import Path
ROOT=Path(r"E:\DEV\Codex-web")
PROFILE=Path(os.environ["APPDATA"])/"web-mcp-assistant"
CANDIDATE=ROOT/"dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4/win-unpacked"
OUTDIR=ROOT/".coding-tools/reports/parallel-native-first-20261012/canary/r4"
ACTION="act_65fa937277dd4963a5ca39ffe9e291ec"; ATTEMPT="try_8a7f3fedcddd4de8a1267eb87a7e39ed"; UNKNOWN="rcpt_3c774da48ff34d34a342c824d8dc94b8"
TASK="task_fd7cb4192b7144bebec0275e66d5eb95"; DEVICE="4c4b7a5b-7744-49ae-a490-78a528a00471"; WORKSPACE="workspace_f93b5bac9dc74fae9cea66f44c4ebc94"; GENERATION="generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
PROCESS="8vZ_MQ-kNrTus9ch"; SERVER="MSZYKc9xLwRhDOMM"; EPOCH="activation-mv5cvpnu-2ddc4f6edfe0487ec46a1594cb87218d"; CONTRACT="0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4"
RUN="e8cef362cfe94b0ba733b73a75fbe09d"; WAVE="4987ffee3e1b4781b313b52ba2700717"; PREIMAGE="03e980c6120541672b4ac1a642c48797e514c90f1235475ee7d83b32edf0cf20"; POSTIMAGE="59609162479b3a662adfefe82646a4d43302a4790de10f67d533368f68f1b8a5"
TARGET=ROOT/"tests/fixtures/native-first-canary/file-019.txt"; CONTEXT=ROOT/".coding-tools/task-contexts/2f4604b5adda953cd683f9d3.json"; LEDGER=ROOT/".coding-tools/orchestration/ledger.sqlite3"
def req(x,c):
    if not x: raise RuntimeError(c)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def snap():
    s=r'''import json,sqlite3,subprocess
from pathlib import Path
pid=int(subprocess.check_output(["systemctl","--user","show","codex-control-plane.service","--property=MainPID","--value"],text=True))
env=dict(x.split("=",1) for x in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in x)
c=sqlite3.connect(Path(env["CONTROL_PLANE_DB"]).resolve().as_uri()+"?mode=ro",uri=True); c.row_factory=sqlite3.Row; c.execute("PRAGMA query_only=ON")
a="__A__"; t="__T__"; d="__D__"
def one(q,p): r=c.execute(q,p).fetchone(); return dict(r) if r else None
print(json.dumps({"pid":pid,"action":one("SELECT * FROM actions WHERE action_id=?",(a,)),"receipts":[dict(r) for r in c.execute("SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id",(a,))],"attempts":[dict(r) for r in c.execute("SELECT * FROM delivery_attempts WHERE action_id=?",(a,))],"task":one("SELECT * FROM mcp_task_sessions WHERE task_id=?",(t,)),"writer":one("SELECT * FROM mcp_task_writer_leases WHERE task_id=?",(t,)),"node":one("SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms FROM nodes WHERE device_id=?",(d,))},separators=(",",":")))
'''.replace("__A__",ACTION).replace("__T__",TASK).replace("__D__",DEVICE)
    r=subprocess.run(["ssh.exe","-T","-o","BatchMode=yes","-o","ConnectTimeout=5","-o","StrictHostKeyChecking=yes","svhome@100.116.112.22","python3","-"],input=s,text=True,capture_output=True,timeout=20)
    req(r.returncode==0 and len(r.stdout)<196608,"SERVER_READONLY_SNAPSHOT_FAILED"); return json.loads(r.stdout)
def validate(s):
    a=s["action"]; req(s["pid"]==970133,"SERVING_PROCESS_CHANGED")
    req(a and a["action_id"]==ACTION and a["device_id"]==DEVICE and a["workspace_id"]==WORKSPACE and a["workspace_generation"]==GENERATION and a["delivery_state"]=="reconcile_required" and a["settled_at_ms"] is None,"EXACT_ACTION_NOT_RECONCILABLE")
    req(len(s["attempts"])==1 and s["attempts"][0]["attempt_id"]==ATTEMPT,"ATTEMPT_LINEAGE_CHANGED")
    rs=s["receipts"]; req(len(rs)==1 and rs[0]["receipt_id"]==UNKNOWN and rs[0]["receipt_state"]=="unknown" and rs[0]["local_handle"]=="","UNKNOWN_RECEIPT_CHANGED")
    req(s["task"] and s["task"]["closed_at_ms"] is None and s["task"]["workspace_generation"]==GENERATION,"TASK_NOT_OPEN")
    req(s["writer"] and s["writer"]["released_at_ms"] is None and s["writer"]["lease_generation"]==1,"WRITER_CHANGED")
    n=s["node"]; req(n and n["readiness"]=="ready" and n["runtime_instance_id"]==PROCESS and n["mcp_server_instance_id"]==SERVER and n["activation_epoch"]==EPOCH,"NODE_NOT_READY")
    return a
def local():
    req(TARGET.exists() and sha(TARGET)==POSTIMAGE,"POSTIMAGE_MISMATCH")
    x=json.loads(CONTEXT.read_text(encoding="utf-8")); o=x["orchestration"]; req(o["run_id"]==RUN and o["wave_id"]==WAVE and o["orchestration_state"]=="ACCEPTING" and len(x["modified_files"])==1 and x["modified_files"][0]["path"].endswith("file-019.txt"),"LOCAL_WORKFLOW_EVIDENCE_CHANGED")
    c=sqlite3.connect(LEDGER); c.row_factory=sqlite3.Row; r=c.execute("SELECT * FROM idempotency_records WHERE idempotency_key=?",("cpap_18aea322bb04475fa067299da53e2aa4e06e471b728251ecfd946343",)).fetchone(); c.close()
    req(r and r["status"]=="completed" and r["process_instance_id"]==PROCESS and r["run_id"]==RUN and r["wave_id"]==WAVE,"LEDGER_WORKFLOW_NOT_COMPLETED")
    return {"context_sha256":sha(CONTEXT),"ledger_sha256":sha(LEDGER),"postimage_sha256":POSTIMAGE,"run_id":RUN,"wave_id":WAVE}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--execute",action="store_true",required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    req(a.output.parent==OUTDIR and not a.output.exists(),"NEW_OUTPUT_REQUIRED")
    action=validate(snap()); evidence=local()
    payload={"schema_version":1,"operation_kind":"control_plane_approved_patch","code":"CONTROL_PLANE_APPROVED_PATCH_RECEIPT_RECONCILED","diagnostic_code":"CONTROL_PLANE_APPROVED_PATCH_TIMEOUT_AFTER_LOCAL_WORKFLOW_COMPLETION","effect_observed":True,"local_semantic_acceptance":False,"original_unknown_receipt_id":UNKNOWN,"original_unknown_receipt_preserved":True,"action_id":ACTION,"attempt_id":ATTEMPT,"task_id":TASK,"runtime_identity":{"activation_epoch_id":EPOCH,"process_instance_id":PROCESS,"server_instance_id":SERVER,"tool_contract_sha256":CONTRACT},"file":{"path":"tests/fixtures/native-first-canary/file-019.txt","preimage_sha256":PREIMAGE,"postimage_sha256":POSTIMAGE,"postimage_verified":True},**evidence}
    spec=importlib.util.spec_from_file_location("r4_agent",CANDIDATE/"resources/resources/control-plane/node_agent.py"); req(spec and spec.loader,"NODE_AGENT_REQUIRED"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    config=m._config(PROFILE/"control-plane-node.json"); entry={"receipt":{"action_id":ACTION,"attempt_id":ATTEMPT,"receipt_state":"failed","local_handle":"","payload":payload,"receipt_submitted":False}}
    response=m._submit_receipt(config,entry); req(response.get("receipt_state")=="failed" and response.get("delivery_state")=="settled","TERMINAL_RECEIPT_REJECTED")
    after=snap(); req(after["action"]["delivery_state"]=="settled" and after["action"]["settled_at_ms"] is not None,"ACTION_NOT_SETTLED"); req(len(after["receipts"])==2 and any(r["receipt_id"]==UNKNOWN for r in after["receipts"]) and any(r["receipt_state"]=="failed" for r in after["receipts"]),"RECEIPTS_NOT_PRESERVED")
    out={"operation":"reconcile_r4_patch019","ok":True,"receipt_state":"failed","central_delivery_state":"settled","original_unknown_receipt_preserved":True,"action_replayed":False,"response":{k:response.get(k) for k in ("receipt_id","action_id","attempt_id","receipt_state","delivery_state")},"payload_sha256":hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"evidence":evidence,"observed_at_ms":int(time.time()*1000)}
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"operation":out["operation"],"ok":True,"output":str(a.output),"receipt_state":"failed","central_delivery_state":"settled"}))
if __name__=="__main__":
    try: main()
    except Exception as e: print(json.dumps({"operation":"reconcile_r4_patch019","ok":False,"error_code":str(e) if isinstance(e,RuntimeError) else type(e).__name__})); raise SystemExit(1)
