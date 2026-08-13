from pathlib import Path
import json
import sys

sys.path.insert(0, r"E:\DEV\Tools-Codex-web\resources\coding-tools-mcp")
from coding_tools_mcp.server import Runtime

run_id = "5757d8ea9440481fb69f1ac78571dfa3"
runtime = Runtime(Path(r"E:\DEV\Tools-Codex-web"), permission_mode="safe")
try:
    result = runtime.task_control({
        "action": "accept",
        "run_id": run_id,
        "reason": "ChatWeb Sol final acceptance: production deterministic smoke passed with zero project-source changes, proof PASS, and audit chain integrity OK.",
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))
finally:
    runtime.close()

