"""Content-free snapshot of the current isolated MXC boot only."""
import datetime
import json
import os
import re
import stat
import time
from pathlib import Path

root = Path(os.environ["TMP"])
state = root / "wxc-wsb" / "state-aware"
fresh = [item for item in state.iterdir() if re.fullmatch(r"[0-9a-f]{8}", item.name)
         and item.is_dir() and time.time() - item.stat().st_ctime < 300]
def bounded(path):
    if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
        return ""
    with path.open("rb") as stream:
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(max(0, size - 65536))
        return stream.read(65536).decode("utf-8", "replace")

result = {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "current_sandbox_count": len(fresh)}
if len(fresh) == 1:
    current = fresh[0]
    log = current / "daemon.log"
    if log.is_file():
        content = bounded(log)
        markers = ("[daemon] launching", "[daemon] rendezvous: guest at ", "[daemon] 4 TCP connections established",
                   "Ready", "Error: launch VM", "Error: rendezvous failed", "Error: connect to guest agent",
                   "WindowsSandbox.exe exited with")
        result["daemon_markers"] = [marker for marker in markers if marker in content]
        result["vm_exit_codes"] = [int(value) for value in re.findall(r"WindowsSandbox\.exe exited with (-?\d{1,10})", content)
                                    if -2147483648 <= int(value) <= 2147483647]
    bootstrap = root / "wxc-wsb-stateaware-rendezvous" / "bootstrap.log"
    if bootstrap.is_file() and bootstrap.stat().st_mtime >= current.stat().st_ctime:
        content = bounded(bootstrap)
        markers = ("[guest] starting", "authentication nonce loaded", "firewall pre-authorized", "listening on",
                   "host connected from", "firewall locked down", "ERROR", "FATAL")
        result["bootstrap_markers"] = [marker for marker in markers if marker in content]
    else:
        result["bootstrap_current"] = False
print(json.dumps(result, separators=(",", ":")))
