"""Inspect exact warm request idempotency/Job without replay or content output."""
import hashlib
import json
from pathlib import Path
import sqlite3
import zlib
import traceback

ROOT = Path(r"E:\Github\Tools-Codex-web")
PROFILE = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant")
ACTION = "act_fc024ff0b54c4a8ba4c7c7b0228a7e76"
ATTEMPT = "try_89bba4cdf2d94c0d8fee58111cd56839"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


try:
    journal = json.loads((PROFILE / "control-plane-node.json.exec-journal.json").read_text())
    entries = [entry for entry in journal["entries"].values() if entry.get("action_id") == ACTION]
    require(len(entries) == 1 and entries[0]["attempt_id"] == ATTEMPT, "EXACT_REQUEST_REQUIRED")
    request = entries[0]["request"]
    material = {key: request[key] for key in ("action_id", "attempt_id", "writer_lease_generation", "operation", "argv",
                "timeout_ms", "max_output_bytes", "facade_contract", "yield_time_ms", "wait_ms")}
    material["task_id"] = request["task_id"].strip()
    for key in ("command_id", "job_id", "local_handle", "consumer_id", "signal", "run_id", "wave_id", "cwd"):
        material[key] = request[key] or ""
    native_key = "cpex_" + hashlib.sha256(json.dumps(material, ensure_ascii=False, sort_keys=True,
                                                    separators=(",", ":")).encode()).hexdigest()[:56]
    with sqlite3.connect((ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        row = db.execute("SELECT * FROM idempotency_records WHERE idempotency_key=?", (native_key,)).fetchone()
        require(row is not None, "EXACT_IDEMPOTENCY_NOT_FOUND")
        data = dict(row)
        result = {"phase": "warm_native_observation", "action_id": ACTION, "attempt_id": ATTEMPT,
                  "native_idempotency_key": native_key, "idempotency_fields": sorted(data),
                  "idempotency": {key: data.get(key) for key in ("operation", "status", "error_code", "process_instance_id", "started_at", "finished_at")}}
        for key in ("result_json", "response_json", "metadata_json", "summary_json"):
            value = data.get(key)
            if value:
                parsed = json.loads(value)
                result[key + "_keys"] = sorted(parsed) if isinstance(parsed, dict) else type(parsed).__name__
                if isinstance(parsed, dict):
                    result[key + "_safe"] = {name: parsed.get(name) for name in ("command_id", "job_id", "status", "exit_code", "timed_out")}
                    command = parsed.get("command")
                    if isinstance(command, dict):
                        result[key + "_command_safe"] = {name: command.get(name) for name in ("id", "job_id", "status", "exit_code")}
        result["summary_codec"] = data.get("summary_codec")
        if data.get("summary_blob"):
            decoded = json.loads(zlib.decompress(data["summary_blob"]))
            result["summary_blob_keys"] = sorted(decoded)
            result["summary_blob_safe"] = {name: decoded.get(name) for name in ("command_id", "job_id", "status", "exit_code", "timed_out")}
            tool = decoded.get("tool_result", {})
            result["tool_result_keys"] = sorted(tool)
            structured = tool.get("structuredContent", {})
            result["structured_keys"] = sorted(structured)
            result["structured_safe"] = {name: structured.get(name) for name in ("command_id", "job_id", "status", "exit_code", "timed_out", "truncated", "run_id", "wave_id")}
            owner = structured.get("execution_owner")
            result["execution_owner_type"] = type(owner).__name__
            result["execution_owner_keys"] = sorted(owner) if isinstance(owner, dict) else []
            result["execution_owner_safe"] = {name: owner.get(name) for name in ("job_id", "run_id", "wave_id", "runtime_instance_id")} if isinstance(owner, dict) else {}
            result["stdout_type"] = type(structured.get("stdout")).__name__
            result["stderr_type"] = type(structured.get("stderr")).__name__
            result["stdout_keys"] = sorted(structured["stdout"]) if isinstance(structured.get("stdout"), dict) else []
            result["stderr_keys"] = sorted(structured["stderr"]) if isinstance(structured.get("stderr"), dict) else []
            result["output_refs_keys"] = sorted(structured["output_refs"]) if isinstance(structured.get("output_refs"), dict) else []
            result["content_types"] = [type(item.get("text")).__name__ for item in tool.get("content", []) if isinstance(item, dict)]
            for item in tool.get("content", []):
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    try:
                        text_payload = json.loads(item["text"])
                        result["content_json_keys"] = sorted(text_payload) if isinstance(text_payload, dict) else []
                        if isinstance(text_payload, dict):
                            result["content_stdout_type"] = type(text_payload.get("stdout")).__name__
                    except ValueError:
                        result["content_json"] = False
            if isinstance(structured.get("command"), dict):
                result["structured_command_keys"] = sorted(structured["command"])
                result["structured_command_safe"] = {name: structured["command"].get(name) for name in ("id", "job_id", "status", "exit_code")}
        recent = db.execute("SELECT job_id,command_id,root_pid,lifecycle_state,started_at,finished_at "
                            "FROM managed_process_jobs WHERE owner='control-plane-exec-bridge' ORDER BY started_at DESC LIMIT 3").fetchall()
        result["recent_jobs"] = [dict(item) for item in recent]
        metadata = db.execute("SELECT metadata_json FROM managed_process_jobs WHERE job_id=?", ("771c4ec8b0d1488fb495dcb6af64bf56",)).fetchone()
        parsed_metadata = json.loads(metadata[0])
        result["job_metadata_keys"] = sorted(parsed_metadata)
    result.update(ok=True, ledger_mutated=False, command_replayed=False)
    print(json.dumps(result, separators=(",", ":")))
except Exception as error:
    print(json.dumps({"phase": "warm_native_observation_failed", "ok": False,
                      "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__,
                      "source_line": traceback.extract_tb(error.__traceback__)[-1].lineno}, separators=(",", ":")))
    raise SystemExit(1) from None
