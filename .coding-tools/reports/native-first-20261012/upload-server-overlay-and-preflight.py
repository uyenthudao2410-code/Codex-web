"""Upload reviewed inert metadata artifacts then run read-only preflight only."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
REMOTE = "/home/svhome/.local/lib/codex-control-plane/releases"
SSH = r"C:\WINDOWS\System32\OpenSSH\ssh.exe"
TARGET = "svhome@100.116.112.22"
OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=yes"]
receipt = json.loads((OUT / "server-overlay-preparation.json").read_text(encoding="utf-8"))
name = receipt["verification"]["release_name"]
suffix = name.rsplit("-", 1)[-1]
helper_sha256 = hashlib.sha256((OUT / "deploy-server-metadata-overlay.py").read_bytes()).hexdigest()
review_suffix = suffix + "-" + helper_sha256[:12]
files = [(Path(receipt["candidate_archive"]), REMOTE + "/" + name + ".tar.gz"),
         (OUT / "server-overlay-preparation.json", REMOTE + "/.native-first-" + review_suffix + ".json"),
         (OUT / "deploy-server-metadata-overlay.py", REMOTE + "/.native-first-" + review_suffix + ".py")]
for path, _target in files:
    if path.suffix == ".py":
        ast.parse(path.read_bytes(), filename=path.name)
records = [{"path": target, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path, target in files]
source = '''
import hashlib,json,os,sys
from pathlib import Path
item=json.loads(sys.argv[1]); p=Path(item["path"])
if p.parent!=Path("/home/svhome/.local/lib/codex-control-plane/releases") or p.is_symlink(): raise RuntimeError("UPLOAD_TARGET_INVALID")
data=sys.stdin.buffer.read(33554433)
if len(data)>33554432 or hashlib.sha256(data).hexdigest()!=item["sha256"]: raise RuntimeError("UPLOAD_CONTENT_INVALID")
if p.exists():
 if hashlib.sha256(p.read_bytes()).hexdigest()!=item["sha256"]: raise RuntimeError("EXISTING_ARTIFACT_DIFFERS")
else:
 os.umask(0o077)
 with p.open("xb") as f:f.write(data)
 p.chmod(0o600)
print(json.dumps({"operation":"inert_native_overlay_upload","ok":True,"path":str(p),"sha256":item["sha256"]}))
'''
# argv is escaped for the remote POSIX shell with shlex; no secret arguments.
import shlex
uploaded = []
for (path, _target), record in zip(files, records):
    command = "python3 -B -c " + shlex.quote(source) + " " + shlex.quote(json.dumps(record, separators=(",", ":")))
    result = subprocess.run([SSH, *OPTIONS, TARGET, command], input=path.read_bytes(), capture_output=True, timeout=30, check=False)
    try:
        projection = json.loads(result.stdout)
        assert result.returncode == 0 and projection.get("operation") == "inert_native_overlay_upload" and projection.get("ok") is True
    except Exception:
        print(json.dumps({"ok": False, "error_code": "INERT_UPLOAD_FAILED", "runtime_mutations": False}))
        sys.exit(1)
    uploaded.append(projection)
command = "python3 -B " + shlex.quote(files[2][1]) + " --receipt " + shlex.quote(files[1][1])
result = subprocess.run([SSH, *OPTIONS, TARGET, command], capture_output=True, timeout=60, check=False)
try:
    preflight = json.loads(result.stdout)
    assert preflight.get("operation") in {"native_first_overlay_readonly_preflight", "native_first_overlay_preflight"}
except Exception:
    preflight = {"ok": False, "error_code": "NO_SANITIZED_PREFLIGHT_RESPONSE", "ssh_exit_code": result.returncode}
report = {"operation": "native_overlay_inert_upload_and_preflight", "ok": result.returncode == 0 and preflight.get("ok") is True,
          "uploaded_artifacts": records, "upload_receipts": uploaded, "preflight": preflight,
          "runtime_mutations": False, "authority_mutations": False,
          "deployment_helper_sha256": helper_sha256,
          "root_execute_command": command + " --execute"}
with (OUT / ("server-overlay-upload-preflight-" + helper_sha256[:12] + ".json")).open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(report, handle, indent=2)
    handle.write("\n")
print(json.dumps({"ok": report["ok"], "preflight": preflight, "root_execute_command": report["root_execute_command"], "runtime_mutations": False}, separators=(",", ":")))
sys.exit(0 if report["ok"] else 1)
