"""Local bundle preparation with synthetic public receipts; no SSH or live IPC."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r13_5h_transport",HERE/"root-canary-ssh.py")
t = importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.now=int(time.time()*1000)
        self.proof={"observed_at_ms":self.now-1,"source_head":"2c554f59cb7b8ffc86ce5e0e28076c792777642f",
            "preimage_sha256":"a"*64,"checker_sha256":"b"*64,"old_run_sha256":"c"*64,
            "old_wave_sha256":"d"*64,"no_active_jobs":True}
        self.native={"ok":True,"kind":"r13_5h_query_only_native_preflight","native_preflight":self.proof,
            "package":{"app_asar_sha256":t.R13_5H_ARCHIVE_SHA,"source_freeze_sha256":t.R13_5H_FREEZE_SHA,"matched_files":17},
            "activation_epoch":"epoch_new","runtime_instance_id":"process_new","mcp_server_instance_id":"server_new",
            "contract_version":"sha256:"+t.NATIVE_SHA,"native_tool_contract_sha256":t.NATIVE_SHA}
        self.receipt={"ok":True,"phase":"r13_5h_intake_reopened","host":"100.116.112.22",
            "service":"codex-control-plane.service","admission":"scoped_pilot",
            "source_revision":"9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c",
            "binding_id":"bind_3e05bf64cb3e4bab93d930ae1692bebb","device_id":"72ceec2d-e3f2-472f-8e3c-99fffe053035",
            "workspace_id":"workspace_dda1d78e9a21402aa6213f72af64f788","workspace_generation":"generation_c2f13e8d02344cf6a38a3f42ecfa59b6",
            "root":r"E:\Github\Tools-Codex-web","profile":"web-mcp-assistant","duration_ms":18000000,
            "prior_marker_sha256":t.AUTHORITY_PRIOR_SHA,"prior_marker_unchanged":True,"deployed":False,"service_restarted":False,
            "requested_at_ms":self.now-1000,"expires_at_ms":self.now+17999000,"context_id":"ctx_new","pilot_id":"pilot_new",
            "service_instance_id":"cp_new","approval_id":"call_a60e931056bd402b997c6c10b0796d81","next_marker_sha256":"e"*64}
        self.authority={"public_receipts":[self.receipt]}
        self.pins={key:self.receipt[key] for key in ("requested_at_ms","expires_at_ms","context_id","pilot_id","service_instance_id","approval_id")}
        self.pins.update({key:self.native[key] for key in ("activation_epoch","runtime_instance_id","mcp_server_instance_id","contract_version","native_tool_contract_sha256")})
        self.pins.update(native_preflight={**self.proof,"receipt_sha256":t.sha(t.canonical(self.native))},
            authority_receipt_sha256=t.sha(t.canonical(self.authority)),authority_marker_sha256=self.receipt["next_marker_sha256"])
        helpers=[]
        for name in ("r13_5h_mcp_canary.py","patch-envelope.txt"):
            raw=(HERE/name).read_bytes();(self.root/name).write_bytes(raw)
            helpers.append({"path":name,"sha256":t.sha(raw),"bytes":len(raw)})
        (self.root/"helper-manifest.json").write_bytes(t.canonical({"files":helpers}))

    def prepare(self):
        for name,value in (("pins.json",self.pins),("native.json",self.native),("authority.json",self.authority)):
            (self.root/name).write_bytes(t.canonical(value))
        args=argparse.Namespace(pins=str(self.root/"pins.json"),native_preflight=str(self.root/"native.json"),
            expected_native_preflight_sha256=t.sha(t.canonical(self.native)),authority_receipt=str(self.root/"authority.json"),
            expected_authority_receipt_sha256=t.sha(t.canonical(self.authority)))
        with patch.object(t,"HERE",self.root):return t.prepare(args)

    def test_dynamic_receipts_form_pinned_six_file_local_bundle(self):
        result=self.prepare()
        self.assertIs(result["remote_mutation"],False)
        self.assertEqual(set(result["files"]),{"r11_common.py","r13_5h_mcp_canary.py","patch-envelope.txt","pins.json","native-preflight.json","authority-receipt.json"})

    def test_native_identity_not_just_preflight_fields_must_match(self):
        self.pins["runtime_instance_id"]="wrong"
        with self.assertRaises(t.Failure) as error:self.prepare()
        self.assertEqual(error.exception.code,"AUTHENTICATED_R13_5H_NATIVE_RECEIPT_REQUIRED")

    def test_package_or_receipt_scope_drift_fails_before_bundle_creation(self):
        self.native["package"]["matched_files"]=12
        with self.assertRaises(t.Failure):self.prepare()
        self.native["package"]["matched_files"]=17
        self.receipt["profile"]="wrong"
        self.pins["authority_receipt_sha256"]=t.sha(t.canonical(self.authority))
        with self.assertRaises(t.Failure):self.prepare()
        self.assertEqual(list(self.root.glob("prepared-*")),[])

    def test_short_trial_fails_without_remote_or_local_effect_bundle(self):
        self.pins["expires_at_ms"]=self.now+719999
        self.pins["requested_at_ms"]=self.pins["expires_at_ms"]-18000000
        with self.assertRaises(t.Failure) as error:self.prepare()
        self.assertEqual(error.exception.code,"EXACT_LIVE_60M_WINDOW_REQUIRED")


if __name__=="__main__":unittest.main(verbosity=2)
