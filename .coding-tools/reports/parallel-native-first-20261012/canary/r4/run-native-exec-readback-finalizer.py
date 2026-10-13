"""Finalize a resume whose read-only artifact action lacked a projection.

The prior resume receipt is immutable and already proves Git diff/log and the
approved build.  This helper creates one fresh task solely for the artifact
readback; it never dispatches an exec action and never reuses the prior action
id.  A bounded file-read relay receipt and exact postimage are required.
"""
import argparse, hashlib, importlib.util, json, re, sys, time
from pathlib import Path
if "_BASE_CANARY" not in globals():
    spec = importlib.util.spec_from_file_location("reviewed_native_canary", Path(__file__).with_name("run-native-first-canary.py")); _BASE_CANARY = importlib.util.module_from_spec(spec); spec.loader.exec_module(_BASE_CANARY)
base = _BASE_CANARY
# The reviewed base harness has no build_readback lane because the original
# canary never reached this continuation. Register the existing bounded read
# lane before calling its observer; this is additive and does not change any
# original action or receipt.
base.LANES["build_readback"] = base.READ
FIXTURE = "tests/fixtures/native-first-canary"; PREFIX = "native-exec-readback-finalizer-20261013:"; SHA = re.compile(r"[a-f0-9]{64}"); IDENTIFIER = base.IDENTIFIER
def require(ok, code):
    if not ok: raise RuntimeError(code)
def sha(value): return hashlib.sha256(value).hexdigest()
def error_code(error): return str(error) if isinstance(error, RuntimeError) else type(error).__name__
def emit(phase, **fields): print(json.dumps({"operation":"native_exec_readback_finalizer","phase":phase,"observed_at_ms":int(time.time()*1000),**fields},separators=(",",":")),flush=True)
def artifact():
    data=b"".join(base.fixture_content(i,i<=20).encode() for i in range(1,101)); return "NATIVE_FIRST_CANARY_BUILD_V1 "+sha(data)+"\n"
def prior_value(path, expected):
    raw = _PRIOR_RESUME_BYTES if "_PRIOR_RESUME_BYTES" in globals() else Path(path).read_bytes(); require(isinstance(raw,bytes) and SHA.fullmatch(expected) and sha(raw)==expected,"PRIOR_RESUME_HASH_MISMATCH")
    rows=[json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]; finals=[x for x in rows if x.get("operation")=="native_exec_continuation_resume" and x.get("phase")=="final"]; require(len(finals)==1,"PRIOR_RESUME_FINAL_NOT_UNIQUE"); value=finals[0]
    require(value.get("ok") is False and value.get("error_code")=="KeyError" and value.get("task_closed_verified") is True and value.get("writer_released_verified") is True,"PRIOR_RESUME_FAILURE_NOT_SAFE")
    require(value.get("proof_counts")=={"git_jobs":2,"approved_build":1,"build_readback":0},"PRIOR_RESUME_COUNTS_INVALID")
    proofs=value.get("proofs",{}); require(all(proofs.get(k,{}).get("job_id") for k in ("git_diff","git_log","build")),"PRIOR_RESUME_PROOFS_INCOMPLETE")
    aid=value.get("action_ids",{}).get("build_readback"); require(isinstance(aid,str) and aid.startswith("act_"),"PRIOR_READBACK_ACTION_MISSING")
    require("build_readback" not in proofs,"PRIOR_READBACK_PROOF_ALREADY_PRESENT")
    return {"sha256":expected,"record_count":len(rows),"final":value}
def run(args):
    prior=prior_value(args.prior_resume,args.prior_resume_sha256); port,connection=base.service_state(args); client=base.Mcp(port,base.credential(args,connection)); attempt=PREFIX+args.attempt_id; task_id=generation=None; owned=False; actions={}; proofs={}; outcome={"ok":False,"attempt_id":args.attempt_id,"source_resume":prior,"source_resume_sha256":args.prior_resume_sha256,"workspace_id":args.workspace_id,"workspace_generation":args.workspace_generation,"binding_id":args.binding_id,"activation_epoch":args.activation_epoch,"process_instance_id":args.process_instance_id,"server_instance_id":args.server_instance_id,"local_tool_contract_sha256":args.local_tool_contract_sha256,"proofs":proofs,"semantic_acceptance_performed":False}; started=time.monotonic()
    try:
        require(base.recover(connection,args.principal_id,attempt)==(None,{}),"FINALIZER_ATTEMPT_ALREADY_USED"); contract=base.check_target(args,connection,client); require(connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL",(args.binding_id,)).fetchone()[0]==0,"CURRENT_TARGET_HAS_OPEN_TASK")
        opened=client.call("workspace_context",{"operation":"task_open","binding_id":args.binding_id,"label":"Native exec continuation artifact readback finalizer","idempotency_key":attempt+":task"}); task_id=opened.get("task",{}).get("task_id"); require(isinstance(task_id,str) and re.fullmatch(r"task_[a-f0-9]{32}",task_id),"TASK_HANDLE_INVALID"); lease=client.call("task_control",{"operation":"writer_claim","task_id":task_id}).get("writer_lease",{}); require(lease.get("state")=="held" and lease.get("task_id")==task_id,"WRITER_LEASE_NOT_HELD"); generation=lease["lease_generation"]; owned=True
        result=client.call("workspace_context",{"operation":"read_file","path":FIXTURE+"/build-artifact.txt","start_line":1,"max_lines":20,"max_bytes":4096,"binding_id":args.binding_id,"task_id":task_id,"idempotency_key":attempt+":build_readback","expected_facade_contract":contract}); action_id=result.get("action_id"); require(isinstance(action_id,str) and re.fullmatch(r"act_[a-f0-9]{32}",action_id),"READBACK_ACTION_INVALID"); actions["build_readback"]=action_id; result=base.observe(client,"build_readback",action_id,task_id,generation); file=result.get("file_read",{}).get("file",{}); require(file.get("path")==FIXTURE+"/build-artifact.txt" and file.get("content")==artifact() and file.get("content_sha256")==sha(artifact().encode()) and file.get("truncated") is False,"BUILD_READBACK_NOT_VERIFIED"); _, proof=base.receipt(connection,result,"file_read",args,contract,task_id,generation,"electron-control-plane-file-read-bridge","control_plane_bounded_file_read"); proofs["build_readback"]={**proof,"path":file["path"],"content_sha256":file["content_sha256"]}; outcome["ok"]=True
    except Exception as error: outcome["error_code"]=error_code(error)
    finally:
        if owned and task_id:
            for tool,operation,extra in (("task_control","writer_release",{"reason":"native_exec_readback_finalizer_finished"}),("workspace_context","task_close",{})):
                try: client.call(tool,{"operation":operation,"task_id":task_id,**extra})
                except Exception as error: outcome[operation+"_error"]=error_code(error)
            try: outcome["task_closed_verified"]=connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?",(task_id,)).fetchone()[0] is not None; outcome["writer_released_verified"]=connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL",(task_id,)).fetchone()[0]==0; outcome["ok"]=outcome["ok"] and outcome["task_closed_verified"] and outcome["writer_released_verified"]
            except Exception as error: outcome["cleanup_verification_error"]=error_code(error); outcome["ok"]=False
        outcome.update({"task_id":task_id,"action_ids":actions,"elapsed_seconds":round(time.monotonic()-started,3),"proof_counts":{"build_readback":int("build_readback" in proofs)}}); connection.close(); emit("final",**outcome)
    return 0 if outcome["ok"] else 1
def main():
    parser=argparse.ArgumentParser()
    for field in ("principal-id","grant-id","device-id","workspace-id","binding-id","workspace-generation","pilot-decision-id","activation-epoch","process-instance-id","server-instance-id","local-tool-contract-sha256","facade-contract-sha256","serving-mcp-facade-sha256","serving-node-agent-sha256","prior-resume","prior-resume-sha256","attempt-id","credential-file"): parser.add_argument("--"+field,required=True)
    parser.add_argument("--facade-schema-version",type=int,required=True); parser.add_argument("--service-pid",type=int,required=True); parser.add_argument("--execute-confirmed-readback-finalizer",action="store_true",required=True); args=parser.parse_args(); require(args.execute_confirmed_readback_finalizer and args.facade_schema_version>=32 and args.service_pid>1,"FINALIZER_EXECUTION_ARGUMENT_INVALID"); require(re.fullmatch(r"[a-f0-9]{32}",args.attempt_id),"ATTEMPT_ID_INVALID"); return run(args)
if __name__=="__main__":
    try: sys.exit(main())
    except Exception as error: emit("preflight_failed",ok=False,error_code=error_code(error)); sys.exit(1)
