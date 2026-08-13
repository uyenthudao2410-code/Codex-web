"""Stub Codex App Server for live provider-restart fault injection.

Implements the minimal stdio JSON-RPC surface used by the bridge
(initialize, thread/start, thread/read, thread/resume, turn/start) and emits
turn lifecycle notifications. Thread state is persisted to a JSON file so a
"restarted provider" (a second invocation of this process) can resume the
same thread — exactly like the real App Server persists history.

Env knobs:
  STUB_STATE_FILE            required; JSON file holding threads + server pids
  STUB_CRASH_AFTER_TURN_START "1" to exit(1) right after acknowledging turn/start
  STUB_TURN_COMPLETE_DELAY_S optional delay (seconds) before turn/completed
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path


def _load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"threads": {}, "servers": [], "turns": {}}


def _save_state(path: Path, state: dict) -> None:
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        temp.write_text(payload, encoding="utf-8")
        os.replace(temp, path)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def main() -> int:
    state_file = Path(os.environ.get("STUB_STATE_FILE", ""))
    if not state_file.parent.exists():
        return 2
    crash_after_turn_start = os.environ.get("STUB_CRASH_AFTER_TURN_START", "") == "1"
    complete_delay = float(os.environ.get("STUB_TURN_COMPLETE_DELAY_S", "0.2") or 0)
    process_id = uuid.uuid4().hex[:8]

    state = _load_state(state_file)
    state.setdefault("threads", {})
    state.setdefault("servers", [])
    state.setdefault("turns", {})
    state["servers"].append(process_id)
    _save_state(state_file, state)

    write_lock = threading.Lock()

    def send(message: dict) -> None:
        line = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        with write_lock:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

    def reply(request_id: object, result: dict) -> None:
        send({"jsonrpc": "2.0", "id": request_id, "result": result})

    def notify(method: str, params: dict) -> None:
        send({"jsonrpc": "2.0", "method": method, "params": params})

    def complete_turn(thread_id: str, turn_id: str) -> None:
        time.sleep(max(0.0, complete_delay))
        notify("turn/started", {"threadId": thread_id, "turnId": turn_id})
        notify("item/agentMessage/delta", {"threadId": thread_id, "turnId": turn_id, "delta": "provider-restart-proof"})
        notify(
            "turn/completed",
            {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed"}},
        )
        current = _load_state(state_file)
        turn = current.get("turns", {}).get(turn_id)
        if turn:
            turn["completed"] = True
            _save_state(state_file, current)

    def handle(request: dict) -> None:
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params") if isinstance(request.get("params"), dict) else {}
        if method == "initialize":
            reply(request_id, {"protocolVersion": "2025-11-25", "serverInfo": {"name": "codex-stub", "version": "0.0.0"}})
            return
        if method == "thread/start":
            thread_id = "stub-thread-" + process_id[:6]
            thread = {
                "id": thread_id,
                "sessionId": "stub-session-" + process_id[:6],
                "cwd": str(params.get("cwd", "")),
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "stub",
            }
            state["threads"][thread_id] = thread
            _save_state(state_file, state)
            reply(request_id, {"thread": thread})
            return
        if method in {"thread/read", "thread/resume"}:
            thread_id = str(params.get("threadId", ""))
            thread = state["threads"].get(thread_id)
            if not thread:
                send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32001, "message": "thread not found"}})
                return
            reply(request_id, {"thread": thread})
            return
        if method == "turn/start":
            thread_id = str(params.get("threadId", ""))
            turn_id = "stub-turn-" + str(len(state["turns"]) + 1)
            state["turns"][turn_id] = {"thread_id": thread_id, "process_id": process_id}
            _save_state(state_file, state)
            reply(request_id, {"turn": {"id": turn_id, "status": "inProgress"}})
            if crash_after_turn_start:
                time.sleep(0.05)
                sys.stdout.flush()
                os._exit(1)
            threading.Thread(target=complete_turn, args=(thread_id, turn_id), daemon=True).start()
            return
        if method == "turn/interrupt":
            reply(request_id, {})
            return
        send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"unknown method {method}"}})

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(request, dict) and request.get("jsonrpc") == "2.0" and "id" in request:
            handle(request)
        elif isinstance(request, dict) and request.get("jsonrpc") == "2.0":
            continue  # notifications are ignored
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
