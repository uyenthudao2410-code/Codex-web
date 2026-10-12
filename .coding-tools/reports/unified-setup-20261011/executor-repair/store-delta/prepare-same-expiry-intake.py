"""Prepare a separate same-expiry recovery helper; never execute its main."""
from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parent
source=BASE/'ubuntu-r10-same-window-intake.py'
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='770853b1f6df78550961a04e0a8d01e19c368247d6384acbf6aa6b0bf98358d0'
text=raw.decode().replace('\r\n','\n')
text=text.replace('Same-window owner intake recovery only; default observe is read-only.', 'Same-expiry supported pilot replacement for owner intake recovery; default observe is read-only.')
text=text.replace('No renew/grant/policy/context\noperation, SQL writes', 'No renew/grant/policy/context\noperation or original-marker modification; one supported same-expiry pilot replacement, no SQL writes')
text=text.replace('def same_authority(g, health, snapshot, overview, grant):', 'def same_authority(g, health, snapshot, overview, grant, *, require_original_pilot=True):')
text=text.replace('    g["renewed_authority"](overview, marker)\n', '''    contexts = [row for row in overview["contexts"] if row.get("binding_id") == g["BINDING"]
        and row.get("closed_at_ms") is None and row.get("expires_at_ms",0) > overview["observed_at_ms"]]
    need(len(contexts)==1 and contexts[0]["context_id"]==CONTEXT and contexts[0]["device_id"]==g["DEVICE"]
        and contexts[0]["workspace_id"]==g["WORKSPACE"] and contexts[0]["workspace_generation"]==g["GENERATION"]
        and contexts[0]["expires_at_ms"]==EXPIRY, "ORIGINAL_CONTEXT_CHANGED")
    original = [row for row in overview["scoped_pilot_decisions"] if row.get("decision_id")==PILOT]
    need(len(original)==1, "ORIGINAL_PILOT_MISSING")
    exact_pilot(g, original[0])
    if require_original_pilot:
        need(original[0].get("revoked_at_ms") is None, "ORIGINAL_PILOT_ALREADY_REVOKED")
''',1)
insert='''
REPLACEMENT_REASON="Owner-approved r10 same-expiry runtime recovery; replace pilot revoked by recovery without renewing authority"
RECOVERY_OPERATION="owner_approved_r10_same_expiry_recovery_pilot_v1"

def exact_pilot(g,row):
    need(row.get("binding_id")==g["BINDING"] and row.get("principal_id")==g["PRINCIPAL"]
        and row.get("device_id")==g["DEVICE"] and row.get("workspace_id")==g["WORKSPACE"]
        and row.get("workspace_generation")==g["GENERATION"] and row.get("expires_at_ms")==EXPIRY,
        "PILOT_SCOPE_OR_EXPIRY_CHANGED")

def save_recovery(path, marker):
    import tempfile
    fd,tmp=tempfile.mkstemp(prefix=".same-expiry-",dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,"wb") as handle:
            handle.write(json.dumps(marker,separators=(",",":")).encode());handle.flush();os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally: Path(tmp).unlink(missing_ok=True)

def recovery_identity(g, marker, snapshot, authority_sha, cold_sha):
    need(marker.get("operation")==RECOVERY_OPERATION and marker.get("service_instance_id")==SERVICE_INSTANCE
        and marker.get("binding_id")==g["BINDING"] and marker.get("original_pilot_id")==PILOT
        and marker.get("context_id")==CONTEXT and marker.get("requested_at_ms")==REQUESTED
        and marker.get("expires_at_ms")==EXPIRY and marker.get("original_authority_marker_sha256")==authority_sha
        and marker.get("initial_state")==snapshot and marker.get("cold_family_sha256")==cold_sha
        and marker.get("operator_approved") is True, "RECOVERY_MARKER_CHANGED")
'''
text=text.replace('\ndef main():\n',insert+'\ndef main():\n',1)
text=text.replace('same_authority(g, health, snapshot, overview, grant)\n', 'same_authority(g, health, snapshot, overview, grant, require_original_pilot=False)\n',1)
text=text.replace('            context_id=CONTEXT, pilot_id=PILOT, service_grant_preserved=g["GRANT"],\n',
    '            context_id=CONTEXT, pilot_id=PILOT, original_pilot_id=PILOT, newpilot_id=None, service_grant_preserved=g["GRANT"],\n',1)
block='''    # The supported recovery API revokes the live pilot. Same-ID close/reopen
    # cannot meet this packet's scope; refuse BEFORE calling any owner API.
    raise Refused("SAME_PILOT_RECOVERY_UNSUPPORTED_PREPARED_OBSERVE_ONLY")
'''
assert text.count(block)==1
text=text.replace(block,'',1)
old='''        same_authority(g, health, snapshot, current, g["target"](current))
        target_mode = "recovery" if args.action == "close" else "scoped_pilot"
        if args.action == "reopen": reopen_identity(g, current, args)
        if mode != target_mode: g["api"](origin, token, "/v1/maintenance/admission", {"mode": target_mode})
'''
new='''        same_authority(g, health, snapshot, current, g["target"](current), require_original_pilot=False)
        operation_dir=g["HOME_DIR"] / ".local/state/codex-control-plane/owner-operations/r10-same-expiry-recovery-v1"
        receipt_path=operation_dir / "intake-recovery-public.json"
        if receipt_path.exists():
            recovery=json.loads(g["protected_file"](receipt_path))
            recovery_identity(g,recovery,snapshot,marker_sha,cold_sha)
        else:
            need(args.action=="close" and mode=="scoped_pilot", "CLOSE_PREPARATION_REQUIRED")
            same_authority(g,health,snapshot,current,g["target"](current))
            live=[row for row in current["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"]>current["observed_at_ms"]]
            need(len(live)==1 and live[0]["decision_id"]==PILOT,"EXACT_ORIGINAL_LIVE_PILOT_REQUIRED")
            need(not operation_dir.exists() and not operation_dir.is_symlink(),"RECOVERY_OPERATION_DIRECTORY_EXISTS")
            operation_dir.mkdir(mode=0o700,parents=True)
            recovery={"operation":RECOVERY_OPERATION,"service_instance_id":SERVICE_INSTANCE,"binding_id":g["BINDING"],
                "original_pilot_id":PILOT,"context_id":CONTEXT,"requested_at_ms":REQUESTED,"expires_at_ms":EXPIRY,
                "original_authority_marker_sha256":marker_sha,"initial_state":snapshot,"cold_family_sha256":cold_sha,
                "operator_approved":True,"phase":"close_prepared","newpilot_id":None}
            save_recovery(receipt_path,recovery)
        target_mode = "recovery" if args.action == "close" else "scoped_pilot"
        if args.action=="close":
            need(recovery["phase"] in {"close_prepared","intake_closed"},"CLOSE_PHASE_CHANGED")
            if mode!="recovery": g["api"](origin,token,"/v1/maintenance/admission",{"mode":"recovery"})
            recovery["phase"]="intake_closed"
            save_recovery(receipt_path,recovery)
        else:
            need(recovery["phase"] in {"intake_closed","pilot_prepared","intake_reopened"},"REOPEN_PHASE_CHANGED")
            reopen_identity(g,current,args)
            old=[row for row in current["scoped_pilot_decisions"] if row.get("decision_id")==PILOT]
            need(len(old)==1 and old[0].get("revoked_at_ms") is not None,"ORIGINAL_PILOT_NOT_REVOKED")
            live=[row for row in current["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"]>current["observed_at_ms"]]
            need(len(live)<=1,"UNEXPECTED_LIVE_PILOT")
            if live:
                replacement=live[0];exact_pilot(g,replacement)
                need(replacement.get("reason")==REPLACEMENT_REASON and replacement["decision_id"]!=PILOT
                    and recovery.get("newpilot_id") in {None,replacement["decision_id"]},"REPLACEMENT_PILOT_CHANGED")
            else:
                need(mode=="recovery" and recovery.get("newpilot_id") is None,"REPLACEMENT_OUTCOME_UNKNOWN_NO_REPLAY")
                replacement=g["api"](origin,token,"/v1/scoped-pilot-decisions",{"principal_id":g["PRINCIPAL"],
                    "binding_id":g["BINDING"],"expires_at_ms":EXPIRY,"reason":REPLACEMENT_REASON})
                exact_pilot(g,replacement)
            recovery.update(newpilot_id=replacement["decision_id"],phase="pilot_prepared",activation_epoch=args.expected_activation_epoch)
            save_recovery(receipt_path,recovery)
            if mode!="scoped_pilot": g["api"](origin,token,"/v1/maintenance/admission",{"mode":"scoped_pilot"})
            recovery["phase"]="intake_reopened"
            save_recovery(receipt_path,recovery)
'''
assert text.count(old)==1
text=text.replace(old,new,1)
text=text.replace('same_authority(g, final_health, snapshot, final_overview, g["target"](final_overview))',
    'same_authority(g, final_health, snapshot, final_overview, g["target"](final_overview), require_original_pilot=False)',1)
text=text.replace('        g["emit"]("r10_same_window_intake_closed"', '''        old=[row for row in final_overview["scoped_pilot_decisions"] if row.get("decision_id")==PILOT]
        need(len(old)==1 and old[0].get("revoked_at_ms") is not None,"ORIGINAL_PILOT_REVOCATION_UNPROVEN")
        if args.action=="reopen":
            live=[row for row in final_overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"]>final_overview["observed_at_ms"]]
            need(len(live)==1 and live[0]["decision_id"]==recovery["newpilot_id"],"REPLACEMENT_REOPEN_UNPROVEN")
            exact_pilot(g,live[0]);reopen_identity(g,final_overview,args)
        g["emit"]("r10_same_window_intake_closed"''',1)
text=text.replace('            context_id=CONTEXT, pilot_id=PILOT, requested_at_ms=REQUESTED, expires_at_ms=EXPIRY,\n',
    '            context_id=CONTEXT, pilot_id=PILOT, original_pilot_id=PILOT, newpilot_id=recovery.get("newpilot_id") if args.action=="reopen" else None,\n            requested_at_ms=REQUESTED, expires_at_ms=EXPIRY,\n',1)
text=text.replace('            service_instance_id=SERVICE_INSTANCE, state=snapshot, state_sha256=g["digest"](snapshot),',
    '            service_instance_id=SERVICE_INSTANCE, source_revision=g["REVISION"], package_source_sha256=g["PACKAGE"],\n            service_grant_preserved=g["GRANT"], state=snapshot, state_sha256=g["digest"](snapshot),',1)
target=BASE/'ubuntu-r10-same-expiry-recovery-intake.py'
compile(text,str(target),'exec')
with target.open('xb') as handle:handle.write(text.encode())
manifest={"kind":"prepared_same_expiry_recovery_intake","helper":target.name,"helper_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
    "base_observe_only_sha256":hashlib.sha256(raw).hexdigest(),"frozen_v3_sha256":"a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec",
    "requested_at_ms":1791722898491,"expires_at_ms":1791726498491,"authority_renewed":False,
    "original_marker_modified":False,"prepared_only":True,"live_operations":False}
with (BASE/'r10-same-expiry-recovery-intake-manifest.json').open('x',encoding='utf-8') as handle:json.dump(manifest,handle,indent=2);handle.write('\n')
print(json.dumps(manifest,separators=(',',':')))
