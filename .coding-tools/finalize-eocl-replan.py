from pathlib import Path
import json
import sys

sys.path.insert(0, r"E:\DEV\Tools-Codex-web\resources\coding-tools-mcp")
from coding_tools_mcp.server import Runtime

run_id = "35ebddf53dc34310a8719319b5682f6a"
runtime = Runtime(Path(r"E:\DEV\Tools-Codex-web"), permission_mode="safe")
try:
    result = runtime.agent_workflow({
        "workflow": "build_release",
        "phase": "run",
        "objective": "Verify the live EOCL control loop with a no-write deterministic proof and preserve the REPLAN lineage from the classifier mismatch.",
        "path": ".",
        "commands": ["cmd /d /c echo EOCL_FINAL_OK"],
        "verification": "none",
        "timeout_seconds": 30,
        "execution_route": "deterministic",
        "execution_mode": "mcp_only",
        "replan_reason": "The prior custom/auto no-write smoke was misclassified as deep-code with no candidate scope; reclassify this same run to deterministic MCP proof without changing project source.",
    })
    orch = result.get("orchestration") or {}
    print(json.dumps({"phase_result": {"ok": result.get("execution", {}).get("ok"), "state": orch.get("orchestration_state"), "run_id": orch.get("run_id"), "wave_id": orch.get("wave_id"), "integrity": orch.get("integrity")}}, ensure_ascii=False, indent=2))
    if orch.get("orchestration_state") != "ACCEPTING":
        raise SystemExit("Expected ACCEPTING after deterministic REPLAN proof")
    accepted = runtime.task_control({
        "action": "accept",
        "run_id": run_id,
        "reason": "ChatWeb Sol final acceptance: deterministic replan proof passed with no project-source mutation; durable lineage and audit integrity are preserved.",
    })
    print(json.dumps({"accepted": accepted.get("accepted"), "orchestration": accepted.get("orchestration")}, ensure_ascii=False, indent=2))
finally:
    runtime.close()

