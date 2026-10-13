"""Run the existing packaged smoke and retain sanitized, independent evidence."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

import psutil

REPOSITORY = Path(__file__).resolve().parents[3]
CANDIDATE = REPOSITORY / "dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked"
PRODUCTION_DESCRIPTOR = Path(os.environ["APPDATA"]) / "web-mcp-assistant/recovery-host.json"
REPORT = Path(__file__).with_name("parallel-r4-timefix-smoke-full.json")


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def identity():
    try:
        value = json.loads(PRODUCTION_DESCRIPTOR.read_text(encoding="utf-8-sig"))
        return {"owner_pid": int(value.get("owner_pid") or 0), "instance_id": str(value.get("instance_id") or "")}
    except FileNotFoundError:
        return None


def remember(process, observed):
    try:
        created = process.create_time()
        observed[(process.pid, created)] = {"pid": process.pid, "parent_pid": process.ppid(), "name": process.name(), "created_at_utc": datetime.fromtimestamp(created, timezone.utc).isoformat()}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass


def generation_alive(key):
    try:
        return psutil.Process(key[0]).create_time() == key[1]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def candidate_census():
    found = []
    for process in psutil.process_iter(["pid", "name", "exe", "create_time"]):
        try:
            executable = process.info.get("exe") or ""
            if executable and os.path.commonpath([str(CANDIDATE).lower(), executable.lower()]) == str(CANDIDATE).lower():
                found.append({"pid": process.pid, "name": process.info["name"], "created_at_utc": datetime.fromtimestamp(process.info["create_time"], timezone.utc).isoformat()})
        except (psutil.Error, ValueError):
            pass
    return sorted(found, key=lambda item: item["pid"])


def main():
    if REPORT.exists():
        raise RuntimeError("Existing evidence receipt must be preserved")
    started = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    product = json.loads((REPOSITORY / "package.json").read_text(encoding="utf-8"))["build"]["productName"]
    hashes = {
        "executable": digest(CANDIDATE / (product + ".exe")),
        "app_asar": digest(CANDIDATE / "resources/app.asar"),
        "source_smoke_script": digest(REPOSITORY / "scripts/packaged-recovery-smoke.js"),
        "source_resource_verifier": digest(REPOSITORY / "scripts/verify-packaged-resources.js"),
        "source_package_parity_receipt": digest(Path(__file__).with_name("parallel-r4-timefix-parity.json")),
    }
    before = identity()
    census_before = candidate_census()
    temp_root = Path(tempfile.gettempdir())
    profiles_before = {str(item) for item in temp_root.glob("webmcp-packaged-recovery-*")}
    profiles_observed = set()
    env = os.environ.copy()
    env["CODEX_PACKAGED_APP_ROOT"] = str(CANDIDATE)
    observed = {}
    timeout = False
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen([r"C:\Program Files\nodejs\node.exe", "scripts/packaged-recovery-smoke.js"], cwd=REPOSITORY, env=env, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
        tracked_root = psutil.Process(process.pid)
        remember(tracked_root, observed)
        deadline = time.monotonic() + 120
        while process.poll() is None and time.monotonic() < deadline:
            try:
                for child in tracked_root.children(recursive=True):
                    remember(child, observed)
            except psutil.Error:
                pass
            profiles_observed.update(str(item) for item in temp_root.glob("webmcp-packaged-recovery-*") if str(item) not in profiles_before)
            time.sleep(0.1)
        if process.poll() is None:
            timeout = True
            # Kill only exact fixture generations observed beneath this run.
            for key in reversed(list(observed)):
                if generation_alive(key):
                    try:
                        psutil.Process(key[0]).kill()
                    except psutil.NoSuchProcess:
                        pass
        process.wait(timeout=10)
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read()
        err = stderr.read()
    try:
        result = json.loads(out.decode("utf-8").strip())
    except (ValueError, UnicodeError):
        result = None
    after = identity()
    census_after = candidate_census()
    lingering = [observed[key] for key in observed if generation_alive(key)]
    remaining_profiles = sorted(str(item) for item in temp_root.glob("webmcp-packaged-recovery-*") if str(item) not in profiles_before)
    report = {
        "schema_version": 1,
        "observed_git_head": head,
        "capture_started_utc": started,
        "capture_finished_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "isolated temporary packaged recovery profile only; production profile and Scheduled Task untouched",
        "candidate": str(CANDIDATE),
        "command": "CODEX_PACKAGED_APP_ROOT=<parallel-r4-timefix candidate> node scripts/packaged-recovery-smoke.js",
        "sha256": hashes,
        "exit_code": process.returncode,
        "timed_out": timeout,
        "result": result,
        "stdout_sha256": hashlib.sha256(out).hexdigest(),
        "stderr_sha256": hashlib.sha256(err).hexdigest(),
        "stderr_empty": not bool(err),
        "sanitized_failure_codes": sorted(set(re.findall(r"\b(?:PACKAGED|PRODUCTION)_[A-Z_]+", err.decode("utf-8", errors="replace")))),
        "production_descriptor_before": before,
        "production_descriptor_after": after,
        "production_descriptor_stable": before == after,
        "fixture_processes_observed": list(observed.values()),
        "fixture_generations_alive_after": lingering,
        "candidate_process_census_before": census_before,
        "candidate_process_census_after": census_after,
        "profiles_observed": sorted(profiles_observed),
        "profiles_remaining_after": remaining_profiles,
        "cleanup_proof": "existing smoke asserts each owned Recovery Host/MCP/Tunnel PID terminal; independent sampled descendant generation and package process census after exit",
        "sampling_limitation": "100ms descendant sampling can miss short-lived children; the smoke's cleanup assertions additionally cover owned persistent fixture processes",
        "operations": {"production_activation": False, "scheduled_task_mutation": False, "rebuild": False, "source_edit": False, "vm_launch": False},
    }
    report["ok"] = process.returncode == 0 and not timeout and bool(result and result.get("ok")) and before == after and not lingering and not census_after and not remaining_profiles
    with REPORT.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
        target.write("\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
