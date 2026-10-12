"""Offline binary transport smoke with a mocked SSH process and temporary receipts."""
from __future__ import annotations
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shlex
import sys
import tarfile
import tempfile
from unittest import mock
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("root_transport_frozen_smoke",OUT/"root-ssh.py")
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
manifest=json.loads((OUT/"helper-manifest.json").read_text())
seen=[]
def fake_run(argv,**kwargs):
    assert argv[1:5]==["-T","-oBatchMode=yes","-oStrictHostKeyChecking=yes","-oConnectTimeout=15"]
    assert argv[5]=="svhome@100.116.112.22"
    command=shlex.split(argv[6]);assert command[:3]==["/usr/bin/python3","-B","-c"]
    expected=json.loads(command[5])
    with tarfile.open(fileobj=io.BytesIO(kwargs["input"]),mode="r:") as archive:
        actual={}
        for member in archive.getmembers():
            raw=archive.extractfile(member).read()
            actual[member.name]={"sha256":hashlib.sha256(raw).hexdigest(),"size_bytes":len(raw)}
    assert actual==expected
    assert set(actual)==set(manifest["helpers"])|{r["name"] for r in manifest["archives"]}
    seen.append({"remote_dir":command[4],"files":sorted(actual),"stdin_bytes":len(kwargs["input"])})
    return type("Result",(),{"returncode":0,"stdout":json.dumps({"phase":"r11_artifacts_staged","ok":True,"host":"100.116.112.22","remote_dir":command[4],"files":expected,"remote_mutation":True}).encode()+b"\n","stderr":b"mocked stderr must remain private"})()
with tempfile.TemporaryDirectory(prefix="r11-binary-transport-smoke-") as temp:
    root=Path(temp)
    for name in manifest["helpers"]:(root/name).write_bytes((OUT/name).read_bytes())
    copy=json.loads(json.dumps(manifest))
    for record in copy["archives"]:record["relative_path"]=str((OUT/record["relative_path"]).resolve())
    (root/"helper-manifest.json").write_text(json.dumps(copy))
    with mock.patch.object(transport,"OUT",root),mock.patch.object(transport.shutil,"which",return_value="ssh-fixture"),mock.patch.object(transport.subprocess,"run",side_effect=fake_run),mock.patch.object(sys,"argv",["root-ssh.py","stage","--remote-dir","/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T000000Z"]),redirect_stdout(io.StringIO()) as stdout:
        transport.main()
    value=json.loads(stdout.getvalue())
    assert value["ssh_returncode"]==0 and value["stderr_disclosed"] is False
    assert "mocked stderr" not in stdout.getvalue()
    paths=list((root/"remote-receipts").glob("*.json"));assert len(paths)==1
    assert json.loads(paths[0].read_text())["stderr_disclosed"] is False
receipt={"operation":"offline_binary_ssh_transport_smoke","captured_at_utc":datetime.now(timezone.utc).isoformat(),
         "transport_sha256":hashlib.sha256((OUT/"root-ssh.py").read_bytes()).hexdigest(),
         "manifest_sha256":hashlib.sha256((OUT/"helper-manifest.json").read_bytes()).hexdigest(),
         "checks_passed":["strict_hostcheck_batchmode_fixed_argv","binary_tar_all4_helpers_and_both_pinned_archives","shell_argument_roundtrip","immutable_public_only_receipt","stderr_never_disclosed"],
         "staged_in_fixture":seen,"network_or_ssh_used":False,"external_mutation":False,"temporary_receipts_removed":True}
with (OUT/"transport-smoke-receipt.json").open("x",encoding="utf-8",newline="\n") as handle:json.dump(receipt,handle,sort_keys=True,indent=2);handle.write("\n")
print(json.dumps({"checks_passed":receipt["checks_passed"],"network_or_ssh_used":False,"external_mutation":False,"transport_sha256":receipt["transport_sha256"]},sort_keys=True))
