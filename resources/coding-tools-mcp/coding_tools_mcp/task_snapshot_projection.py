from __future__ import annotations

from typing import Any


def build_task_snapshot_projection(state: dict[str, Any]) -> dict[str, Any]:
    command = state.get("current_command")
    if isinstance(command, dict):
        command = {
            key: command.get(key)
            for key in ("kind", "command", "status", "started_at", "workdir")
        }
    else:
        command = None

    raw_steps = state.get("steps") if isinstance(state.get("steps"), list) else []
    task_steps = [
        {
            "id": str(item.get("id") or "")[:200],
            "text": str(item.get("text") or "")[:4_000],
            "status": str(item.get("status") or "pending")[:100],
            "updated_at": str(item.get("updated_at") or "")[:100],
        }
        for item in raw_steps[-40:]
        if isinstance(item, dict)
    ]

    raw_tests = state.get("test_results") if isinstance(state.get("test_results"), list) else []
    task_tests = [
        {
            "command": str(item.get("command") or "")[:4_000],
            "status": str(item.get("status") or "")[:100],
            "exit_code": item.get("exit_code"),
            "duration_ms": item.get("duration_ms"),
            "summary": str(item.get("summary") or "")[:2_000],
            "finished_at": str(item.get("finished_at") or "")[:100],
        }
        for item in raw_tests[-10:]
        if isinstance(item, dict)
    ]

    raw_modified = state.get("modified_files") if isinstance(state.get("modified_files"), list) else []
    task_modified_files = []
    for item in raw_modified[-20:]:
        if isinstance(item, dict):
            path = str(item.get("path") or "")[:2_000]
            if path:
                task_modified_files.append(
                    {
                        "path": path,
                        "operation": str(item.get("operation") or "update")[:100],
                        "updated_at": str(item.get("updated_at") or "")[:100],
                    }
                )
        else:
            path = str(item or "")[:2_000]
            if path:
                task_modified_files.append(
                    {"path": path, "operation": "update", "updated_at": ""}
                )

    raw_build_report = state.get("last_build_report")
    task_build_report = None
    if isinstance(raw_build_report, dict):
        raw_project = (
            raw_build_report.get("project")
            if isinstance(raw_build_report.get("project"), dict)
            else {}
        )
        raw_artifacts = (
            raw_build_report.get("artifacts")
            if isinstance(raw_build_report.get("artifacts"), list)
            else []
        )
        artifacts = []
        for item in raw_artifacts[:8]:
            if not isinstance(item, dict):
                continue
            artifact_path = str(item.get("path") or "")[:2_000]
            if not artifact_path:
                continue
            artifacts.append(
                {
                    "path": artifact_path,
                    "size": item.get("size"),
                    "sha256": str(item.get("sha256") or "")[:128],
                    "sha384": str(item.get("sha384") or "")[:160],
                    "sha512": str(item.get("sha512") or "")[:192],
                }
            )
        task_build_report = {
            "overall_status": str(raw_build_report.get("overall_status") or "")[:100],
            "failure": str(raw_build_report.get("failure") or "")[:2_000],
            "project": {
                "type": str(raw_project.get("type") or "")[:100],
                "name": str(raw_project.get("name") or "")[:300],
                "version": str(raw_project.get("version") or "")[:100],
            },
            "artifacts": artifacts,
        }

    return {
        "steps": task_steps,
        "test_results": task_tests,
        "modified_files": task_modified_files,
        "current_command": command,
        "failure": str(state.get("failure") or "")[:2_000] or None,
        "last_build_report": task_build_report,
    }
