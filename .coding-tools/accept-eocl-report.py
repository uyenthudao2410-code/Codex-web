from pathlib import Path
import json
import sys

sys.path.insert(0, r"E:\DEV\Tools-Codex-web\resources\coding-tools-mcp")
from coding_tools_mcp.server import Runtime

run_id = "d61c2ccc84e042adada9a93aa8c97603"
runtime = Runtime(Path(r"E:\DEV\Tools-Codex-web"), permission_mode="safe")
try:
    result = runtime.task_control({
        "action": "accept",
        "run_id": run_id,
        "reason": "ChatWeb Sol final acceptance: checkpoint provenance is now rendered from the canonical ledger; focused report test, full 56-test Python suite, 5/5 stability suite, and diff hygiene all passed.",
    })
    print(json.dumps({"accepted": result["accepted"], "orchestration": result["orchestration"]}, ensure_ascii=False, indent=2))
finally:
    runtime.close()

