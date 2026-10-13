"""Read-only serving-source path discovery; excludes raw command/environment."""
import json
from pathlib import Path
import subprocess

source = r'''
import json, os, re, subprocess
from pathlib import Path
result = subprocess.run(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID"], capture_output=True, text=True, timeout=10)
pid = int(result.stdout.strip().split("=", 1)[1])
root = Path(f"/proc/{pid}/cwd").resolve()
environment = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
safe = {"operation": "readonly_serving_source_discovery", "pid": pid, "cwd": str(root), "exe": str(Path(f"/proc/{pid}/exe").resolve()), "python_path_candidates": [], "matching_source_paths": []}
for value in environment.get("PYTHONPATH", "").split(":"):
    path = Path(value).resolve() if value else None
    if path and path.is_relative_to(Path.home().resolve()) and path.is_dir():
        safe["python_path_candidates"].append(str(path))
for path in root.rglob("http_api.py"):
    if path.parent.name == "control_plane" and path.is_relative_to(Path.home().resolve()):
        safe["matching_source_paths"].append(str(path))
        if len(safe["matching_source_paths"]) >= 20:
            break
safe["external_mutations_performed"] = False
print(json.dumps(safe, separators=(",", ":")))
'''
result = subprocess.run([r"C:\WINDOWS\System32\OpenSSH\ssh.exe", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=yes", "svhome@100.116.112.22", "python3", "-B", "-"], input=source.encode(), capture_output=True, timeout=45, check=False)
try:
    report = json.loads(result.stdout)
    assert report.get("operation") == "readonly_serving_source_discovery"
except Exception:
    report = {"ok": False, "error_code": "SOURCE_DISCOVERY_FAILED", "ssh_exit_code": result.returncode}
path = Path(__file__).resolve().with_name("source-discovery.json")
with path.open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(report, handle, indent=2)
    handle.write("\n")
print(json.dumps(report, separators=(",", ":")))
