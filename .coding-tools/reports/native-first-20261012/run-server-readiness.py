"""Run the protected additive observer using strict SSH, save sanitized evidence."""

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
REPORTS = Path(__file__).resolve().parent
OBSERVER = REPORTS / "inspect-server-readiness.py"
SSH = Path(r"C:\WINDOWS\System32\OpenSSH\ssh.exe")
TARGET = "svhome@100.116.112.22"


def git(*arguments):
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("LOCAL_GIT_OBSERVATION_FAILED")
    return result.stdout


def manifest():
    package = ROOT / "control-plane/control_plane"
    current, head = {}, {}
    for path in sorted(package.glob("*.py")):
        current[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        head[path.name] = hashlib.sha256(git("show", "HEAD:control-plane/control_plane/" + path.name)).hexdigest()
    return current, head


def main():
    output = REPORTS / (sys.argv[1] if len(sys.argv) > 1 else "server-readiness.json")
    if output.parent != REPORTS or output.exists():
        raise RuntimeError("REPORT_PATH_EXISTS_OR_OUTSIDE_REPORTS")
    source = OBSERVER.read_bytes()
    ast.parse(source, filename=OBSERVER.name)
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(SSH), "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                             "-o", "StrictHostKeyChecking=yes", TARGET, "python3", "-B", "-"],
                            input=source, capture_output=True, timeout=90, check=False)
    try:
        if len(result.stdout) > 262144:
            raise ValueError()
        report = json.loads(result.stdout)
        if not isinstance(report, dict) or report.get("operation") != "native_first_ubuntu_readonly_readiness":
            raise ValueError()
    except (ValueError, TypeError):
        error = result.stderr.decode("utf-8", errors="replace")
        if re.search(r"Host key verification failed|REMOTE HOST IDENTIFICATION HAS CHANGED|No .* host key is known", error):
            code = "SSH_HOST_KEY_BLOCKED"
        elif re.search(r"Permission denied|publickey", error):
            code = "SSH_CREDENTIAL_UNAVAILABLE"
        elif re.search(r"timed out|No route to host|Connection refused|Could not resolve", error):
            code = "SSH_NETWORK_UNAVAILABLE"
        else:
            code = "SSH_OBSERVER_NO_SANITIZED_RESPONSE"
        report = {"operation": "native_first_ubuntu_readonly_readiness", "ok": False,
                  "error_code": code, "external_mutations_performed": False}
    current, head = manifest()
    report["local_observation"] = {"head": git("rev-parse", "HEAD").decode().strip(),
        "branch": git("branch", "--show-current").decode().strip(), "ssh_target": TARGET,
        "strict_host_key_checking": True, "batch_default_keys": True,
        "observer_sha256": hashlib.sha256(source).hexdigest(), "ssh_exit_code": result.returncode,
        "capture_started_utc": started, "capture_completed_utc": datetime.now(timezone.utc).isoformat(),
        "current_package_python_files_sha256": current, "head_package_python_files_sha256": head}
    remote = report.get("serving_source", {}).get("python_files_sha256", {})
    if remote:
        report["serving_vs_local_current_changed_files"] = sorted(name for name in set(remote) | set(current) if remote.get(name) != current.get(name))
        report["serving_vs_local_head_changed_files"] = sorted(name for name in set(remote) | set(head) if remote.get(name) != head.get(name))
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"report": str(output), "ok": report.get("ok"), "error_code": report.get("error_code"),
                      "ssh_exit_code": result.returncode,
                      "canary_eligible": report.get("codex_web_canary_eligible_under_current_authority"),
                      "canary_blockers": report.get("codex_web_canary_blockers")}, separators=(",", ":")))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", str(error)) else type(error).__name__
        print(json.dumps({"ok": False, "error_code": code}, separators=(",", ":")))
        sys.exit(1)
