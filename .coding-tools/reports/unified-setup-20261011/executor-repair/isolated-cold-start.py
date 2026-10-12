"""One isolated r7 backend run; no shared activation or action replay."""
import hashlib
import json
import sys
sys.dont_write_bytecode = True
import time
import base64
import re
import subprocess
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RESOURCES = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-unified-setup-1011-r7/win-unpacked/resources/resources"
source_mode = "--source" in sys.argv
sys.path.insert(0, str(ROOT / "resources/coding-tools-mcp" if source_mode else RESOURCES / "coding-tools-mcp"))
if source_mode:
    from coding_tools_mcp import windows_mxc_state_aware as source_backend
    source_backend._resource_root = lambda: RESOURCES
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.windows_mxc_state_aware import (
    MxcWindowsSandboxManager, build_mxc_windows_sandbox_invocation,
    cleanup_mxc_windows_sandbox_invocation, _run_child,
)

def emit(**value):
    print(json.dumps(value, separators=(",", ":")), flush=True)

manager = MxcWindowsSandboxManager()
run_original = subprocess.run
def capture_backend(argv, **kwargs):
    result = run_original(argv, **kwargs)
    if result.returncode != 0 and isinstance(argv, list) and "--config-base64" in argv:
        output = kwargs.get("stdout")
        if output is not None and hasattr(output, "seek"):
            output.flush()
            output.seek(0)
            raw = output.read(32769)
            output.seek(0, 2)
            try:
                payload = json.loads(raw)
                message = payload.get("error", {}).get("message", "")
            except (ValueError, TypeError, AttributeError):
                message = ""
            if isinstance(message, str):
                # Only fixed diagnostic categories and Windows HRESULTs leave
                # memory; raw backend text can contain private paths/nonces.
                words = ("timeout", "timed out", "rendezvous", "daemon", "guest", "launch",
                         "process", "not found", "access denied", "busy", "terminated",
                         "bootstrap", "socket", "connection", "ready", "exited", "invalid")
                emit(event="backend_classification", categories=[word for word in words if word in message.lower()],
                     hresults=sorted(set(re.findall(r"0x[0-9a-fA-F]{8}\b", message))), message_length=len(message))
                ready_timeout = re.fullmatch(r"daemon did not become ready within (\d{1,6})s", message)
                if ready_timeout:
                    emit(event="backend_ready_timeout", seconds=int(ready_timeout.group(1)))
    return result
subprocess.run = capture_backend

def classify_log(config):
    sandbox_id = config.get("sandboxId", "")
    if not isinstance(sandbox_id, str) or not re.fullmatch(r"wsb:[0-9a-f]{8}", sandbox_id):
        return
    log = Path(manager._environment()["TMP"]) / "wxc-wsb" / "state-aware" / sandbox_id[4:] / "daemon.log"
    try:
        if any(path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
               for path in (log.parent.parent, log.parent, log)):
            emit(event="daemon_classification", available=False)
            return
        with log.open("rb") as stream:
            stream.seek(0, 2)
            size = stream.tell()
            stream.seek(max(0, size - 65536))
            content = stream.read(65536).decode("utf-8", "replace")
        known = ("Error: launch VM", "Error: rendezvous failed", "Error: connect to guest agent",
                 "timed out waiting for rendezvous", "ready; holding", "waiting for guest",
                 "launching Windows Sandbox", "no VM was launched", "leaving any running VM untouched")
        emit(event="daemon_classification", available=True, bytes=size,
             categories=[phrase for phrase in known if phrase in content],
             vm_exit_codes=[int(code) for code in re.findall(r"WindowsSandbox\.exe exited with (-?\d{1,10})", content)
                            if -2147483648 <= int(code) <= 2147483647])
    except OSError:
        emit(event="daemon_classification", available=False)
original = manager._run_envelope
def observed(config, **kwargs):
    started = time.monotonic()
    emit(event="phase_begin", phase=config.get("phase"))
    try:
        result = original(config, **kwargs)
        emit(event="phase_end", phase=config.get("phase"), ok=True, elapsed_ms=int((time.monotonic()-started)*1000))
        return result
    except ToolFailure as error:
        if config.get("phase") == "start":
            classify_log(config)
        emit(event="phase_end", phase=config.get("phase"), ok=False, code=error.code,
             details={key: error.details[key] for key in ("phase", "backend_error_code") if key in error.details},
             elapsed_ms=int((time.monotonic()-started)*1000))
        raise
manager._run_envelope = observed
invocation = None
try:
    run_test = "--test" in sys.argv
    command = ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"] if run_test else ["node", "--version"]
    emit(event="begin", artifact="source_with_r7_binaries" if source_mode else "r7", command=" ".join(command), workspace=str(ROOT))
    invocation = build_mxc_windows_sandbox_invocation(command, manager=manager,
        workspace_root=ROOT, workdir=ROOT, timeout_ms=60000)
    result = _run_child(invocation, timeout_seconds=75)
    # A version marker is the only permitted output from this fixed probe.
    import re
    output = result.stdout.strip()
    emit(event="command_end", exit_code=result.returncode,
         version=output if re.fullmatch(r"v\d+\.\d+\.\d+", output) else None,
         tap_summary=re.findall(r"^# (?:tests|pass|fail|cancelled|skipped) \d+$", output, re.MULTILINE),
         stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest())
except ToolFailure as error:
    emit(event="failure", code=error.code, details={key: error.details[key]
         for key in ("phase", "backend_error_code") if key in error.details})
    raise SystemExit(1)
finally:
    if invocation is not None:
        emit(event="invocation_cleanup", ok=cleanup_mxc_windows_sandbox_invocation(invocation, abort=True))
    emit(event="manager_cleanup", ok=manager.close())
