from pathlib import Path
import json
import sys

sys.path.insert(0, r"E:\DEV\Tools-Codex-web\resources\coding-tools-mcp")
from coding_tools_mcp.server import Runtime

run_id = "d559e6e5ac0743ada301d282555cabe7"
runtime = Runtime(Path(r"E:\DEV\Tools-Codex-web"), permission_mode="safe")
try:
    result = runtime.task_control({
        "action": "accept",
        "run_id": run_id,
        "reason": "ChatWeb Sol final acceptance: terminal EOCL projection monotonicity fix passed focused tests, full 55-test Python suite, 5/5 stability tests, and diff hygiene.",
    })
    print(json.dumps(result["orchestration"], ensure_ascii=False, indent=2))
finally:
    runtime.close()

