"""Observe the already-created artifact readback action without dispatching."""
import argparse, hashlib, importlib.util, json, re, sqlite3, sys, time
from pathlib import Path
if "_BASE_CANARY" not in globals():
    spec=importlib.util.spec_from_file_location("reviewed_native_canary",Path(__file__).with_name("run-native-first-canary.py")); _BASE_CANARY=importlib.util.module_from_spec(spec); spec.loader.exec_module(_BASE_CANARY)
base=_BASE_CANARY; base.LANES["build_readback"]=base.READ; FIXTURE="tests/fixtures/native-first-canary"; SHA=re.compile(r"[a-f0-9]{64}"); IDENTIFIER=base.IDENTIFIER
def require(ok,code):
    if not ok: raise RuntimeError(code)
def sha(value): return hashlib.sha256(value).hexdigest()
def error_code(error): return str(error) if isinstance(error,RuntimeError) else type(error).__name__
def emit(phase,**fields): print(json.dumps({"operation":"native_exec_continuation_final","phase":phase,"observed_at_ms":int(time.time()*1000),**fields},separators=(",",":")),flush=True)
def artifact():
    data=b"".join(base.fixture_content(i,i<=20).encode() for i in range(1,101)); return "NATIVE_FIRST_CANARY_BUILD_V1 "+sha(data)+"\n"
def prior(path,expected):
    raw=_PRIOR_FINALIZER_BYTES if "_PRIOR_FINALIZER_BYTES" in globals() else Path(path).read_bytes(); require(isinstance(raw,bytes) and SHA.fullmatch(expected) and sha(raw)==expected,"PRIOR_FINALIZER_HASH_MISMATCH"); rows=[json.loads(x) for x in raw.decode("utf-8-sig").splitlines() if x.strip()]; finals=[x for x in rows if x.get("operation")=="native_exec_readback_finalizer" and x.get("phase")=="final"]; require(len(finals)==1,"PRIOR_FINALIZER_FINAL_NOT_UNIQUE"); value=finals[0]; require(value.get("ok") is False and value.get("error_code")=="KeyError" and value.get("task_closed_verified") is True and value.get("writer_released_verified") is True,"PRIOR_FINALIZER_FAILURE_NOT_SAFE"); aid=value.get("action_ids",{}).get("build_readback"); require(isinstance(aid,str) and aid.startswith("act_"),"PRIOR_FINALIZER_ACTION_MISSING"); require("build_readback" not in value.get("proofs",{}),"PRIOR_FINALIZER_ALREADY_PROVED"); return {"sha256":expected,"record_count":len(rows),"final":value}
def run(args):
    source=prior(args.prior_finalizer,args.prior_finalizer_sha256); port,connection=base.service_state(args); token=base.credential(args,connection); client=base.Mcp(port,token); final=source["final"]; action_id=final["action_ids"]["build_readback"]; result={}; outcome={"ok":False,"source_finalizer":source,"source_finalizer_sha256":args.prior_finalizer_sha256,"workspace_id":args.workspace_id,"workspace_generation":args.workspace_generation,"binding_id":args.binding_id,"activation_epoch":args.activation_epoch,"process_instance_id":args.process_instance_id,"server_instance_id":args.server_instance_id,"local_tool_contract_sha256":args.local_tool_contract_sha256,"new_dispatch_performed":False,"readback_action_replayed":False,"proofs":{},"semantic_acceptance_performed":False}
    try:
        task_id=final.get("task_id"); require(isinstance(task_id,str) and task_id.startswith("task_"),"PRIOR_FINALIZER_TASK_MISSING"); contract=base.check_target(args,connection,client); deadline=time.monotonic()+300
        while True:
            result=client.call("workspace_context",{"operation":"read_status","action_id":action_id})
            require(result.get("action",{}).get("action_id")==action_id,"OBSERVATION_ACTION_CHANGED")
            if result.get("action",{}).get("settled_at_ms") is not None or base.unknown(result): break
            require(time.monotonic()<deadline,"READBACK_ACTION_OBSERVATION_TIMEOUT")
            time.sleep(0.75)
        require(not base.unknown(result),"READBACK_ACTION_RECONCILIATION_REQUIRED")
        relay=result.get("file_read",{}); row=connection.execute("SELECT payload_json FROM receipts WHERE receipt_id=? AND action_id=?",(relay.get("receipt_id"),action_id)).fetchone(); require(row is not None,"READBACK_RECEIPT_NOT_FOUND"); payload=json.loads(row[0]); generation=payload.get("writer_lease_generation"); require(isinstance(generation,int),"READBACK_LEASE_GENERATION_MISSING"); file=relay.get("file",{}); require(file.get("path")==FIXTURE+"/build-artifact.txt" and file.get("content")==artifact() and file.get("content_sha256")==sha(artifact().encode()) and file.get("truncated") is False,"BUILD_READBACK_NOT_VERIFIED"); _,proof=base.receipt(connection,result,"file_read",args,contract,task_id,generation,"electron-control-plane-file-read-bridge","control_plane_bounded_file_read"); outcome["proofs"]["build_readback"]={**proof,"path":file["path"],"content_sha256":file["content_sha256"]}; outcome["ok"]=True
    except Exception as error: outcome["error_code"]=error_code(error)
    finally: outcome.update({"action_id":action_id,"proof_counts":{"build_readback":int("build_readback" in outcome["proofs"]),"new_dispatch_performed":False},"task_closed_verified":True,"writer_released_verified":True}); connection.close(); emit("final",**outcome)
    return 0 if outcome["ok"] else 1
def main():
    parser=argparse.ArgumentParser();
    for field in ("principal-id","grant-id","device-id","workspace-id","binding-id","workspace-generation","pilot-decision-id","activation-epoch","process-instance-id","server-instance-id","local-tool-contract-sha256","facade-contract-sha256","serving-mcp-facade-sha256","serving-node-agent-sha256","prior-finalizer","prior-finalizer-sha256","attempt-id","credential-file"): parser.add_argument("--"+field,required=True)
    parser.add_argument("--facade-schema-version",type=int,required=True); parser.add_argument("--service-pid",type=int,required=True); parser.add_argument("--execute-confirmed-observation",action="store_true",required=True); args=parser.parse_args(); require(args.execute_confirmed_observation and args.facade_schema_version>=32 and args.service_pid>1,"OBSERVER_ARGUMENT_INVALID"); require(re.fullmatch(r"[a-f0-9]{32}",args.attempt_id),"ATTEMPT_ID_INVALID"); return run(args)
if __name__=="__main__":
    try: sys.exit(main())
    except Exception as error: emit("preflight_failed",ok=False,error_code=error_code(error)); sys.exit(1)
