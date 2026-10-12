"""Read-only observation of the single already-dispatched r11 canary."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys

sys.dont_write_bytecode = True
CANARY_DIR = Path("/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T163335163457Z")
CANARY_SHA = "b9be1f2fb50b3831442dbf12aaf15f68a2af5286c8ae5bd14b74f0a375b7918a"
ACTION = "act_a0b6b348fd944ea7b9e1eccf0b4c816f"
TASK = "task_d06d0dcedee9447ca8dca049137295aa"


class Failure(Exception):
    def __init__(self, code):
        self.code = code


def require(condition, code):
    if not condition:
        raise Failure(code)


def pinned_canary():
    path = CANARY_DIR / "r11_mcp_canary.py"
    require(os.name == "posix" and path.is_file() and not path.is_symlink()
        and path.stat().st_uid == os.getuid() and stat.S_IMODE(path.stat().st_mode) == 0o600
        and hashlib.sha256(path.read_bytes()).hexdigest() == CANARY_SHA, "FROZEN_REMOTE_CANARY_CHANGED")
    spec = importlib.util.spec_from_file_location("r11_original_observed_canary", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def context_family(database, common, pins, family):
    require(family.get("action_id") == ACTION and family.get("task_id") == TASK, "EXACT_DISPATCHED_FAMILY_REQUIRED")
    require(database.is_absolute() and database.is_file() and not database.is_symlink(), "DATABASE_TARGET_UNSAFE")
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        action = connection.execute("SELECT * FROM actions WHERE action_id=?", (ACTION,)).fetchone()
        require(action is not None, "DISPATCHED_ACTION_NOT_FOUND")
        action = dict(action)
        request = connection.execute("SELECT * FROM work_requests WHERE request_id=?", (action["request_id"],)).fetchone()
        context = connection.execute("SELECT * FROM contexts WHERE context_id=?", (action["context_id"],)).fetchone()
        intents = [dict(row) for row in connection.execute("SELECT * FROM mcp_standing_patch_intents WHERE action_id=?", (ACTION,))]
        links = [dict(row) for row in connection.execute("SELECT * FROM mcp_task_action_links WHERE action_id=?", (ACTION,))]
        task = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (TASK,)).fetchone()
        owner_context = connection.execute("SELECT * FROM contexts WHERE context_id=?", (pins["context_id"],)).fetchone()
        require(request is not None and context is not None and task is not None and owner_context is not None
            and len(intents) == 1 and len(links) == 1, "ACTION_CONTEXT_CAUSAL_LINK_MISSING")
        request, context, task, owner_context = map(dict, (request, context, task, owner_context))
        intent = intents[0]
        require(action["request_id"] == family["request_id"] == intent["request_id"]
            and action["context_id"] == request["context_id"] == context["context_id"]
            and context["context_id"] != pins["context_id"]
            and links[0]["task_id"] == TASK == intent["task_id"]
            and intent["principal_id"] == task["principal_id"] == common.PRINCIPAL
            and intent["authority_mode"] == "standing", "ACTION_CONTEXT_CAUSAL_LINK_CHANGED")
        require(all(row["owner_id"] == owner_context["owner_id"] for row in (action, request, context, intent, task))
            and all(row["binding_id"] == common.BINDING for row in (action, context, intent, task, owner_context))
            and all(row["device_id"] == common.DEVICE and row["workspace_id"] == common.WORKSPACE
                and row["workspace_generation"] == common.GENERATION for row in (action, context, task, owner_context))
            and action["endpoint_id"] == context["endpoint_id"] == owner_context["endpoint_id"], "ACTION_CONTEXT_TARGET_CHANGED")
        require(action["created_at_ms"] == request["created_at_ms"] == context["created_at_ms"] == intent["created_at_ms"]
            and pins["requested_at_ms"] <= context["created_at_ms"] < pins["expires_at_ms"]
            and action["expires_at_ms"] == request["expires_at_ms"] == context["expires_at_ms"] <= pins["expires_at_ms"]
            and context["expires_at_ms"] - context["created_at_ms"] == 600000
            and context["closed_at_ms"] is None and request["canceled_at_ms"] is None, "ACTION_CONTEXT_WINDOW_CHANGED")
        require(connection.execute("SELECT COUNT(*) FROM actions WHERE context_id=?", (context["context_id"],)).fetchone()[0] == 1
            and connection.execute("SELECT COUNT(*) FROM work_requests WHERE context_id=?", (context["context_id"],)).fetchone()[0] == 1,
            "ACTION_CONTEXT_REUSED_BY_OTHER_WORK")
        return context
    finally:
        connection.close()


def authority_view(common, pins, overview, context):
    rows = [row for row in overview["contexts"] if row.get("context_id") == context["context_id"]]
    require(len(rows) == 1 and all(rows[0].get(key) == value for key, value in context.items()), "ACTION_CONTEXT_OVERVIEW_CHANGED")
    # Remove only a fully proven internal context from a copy. The unchanged
    # frozen guard still rejects every other live target context and pilot.
    view = {**overview, "contexts": [row for row in overview["contexts"] if row.get("context_id") != context["context_id"]]}
    common.renewed_authority(view, pins)
    return view


def observed_state():
    canary = pinned_canary()
    common = canary.load_common()
    try:
        pins = canary.pins_input(common)
        marker = canary.private_json(canary.NEXT_OPERATION_DIR / "canary-dispatch.json")
        response = canary.private_json(canary.NEXT_OPERATION_DIR / "canary-dispatch-response.json")
        require(marker.get("pins_sha256") == canary.digest(pins)
            and response.get("action_id") == ACTION and response.get("task_id") == TASK,
            "EXACT_EXISTING_DISPATCH_MARKER_REQUIRED")
        config = common.environment()
        bind = config.get("CONTROL_PLANE_BIND", "127.0.0.1")
        require(bind in {"127.0.0.1", "0.0.0.0", "::", common.HOST}, "SERVICE_BIND_CHANGED")
        origin = "http://" + (common.HOST if bind == common.HOST else "127.0.0.1") + ":" + config.get("CONTROL_PLANE_PORT", "8765")
        token = config["CONTROL_PLANE_OPERATOR_TOKEN"]
        database = Path(config["CONTROL_PLANE_DB"])
        health = common.api(origin, token, "/healthz")
        overview = common.api(origin, token, "/v1/ui/overview")
        grant = common.target(overview)
        family = canary.ids(common, database, marker)
        context = context_family(database, common, pins, family)
        view = authority_view(common, pins, overview, context)
        canary.authority_guard(common, pins, health, view, grant, dispatch=False)
        return canary, common, pins, marker, database, family
    finally:
        if canary._prior_marker_path is not None:
            require(canary.sha(canary._prior_marker_path.read_bytes()) == canary._prior_marker_sha256,
                "PREVIOUS_AUTHORITY_MARKER_CHANGED_DURING_OBSERVATION")


def rejected_receipt(database, family):
    require(family.get("settled") is True and family.get("state") == "settled"
        and family.get("receipt_states") == ["rejected"] and len(family.get("attempt_ids", [])) == 1,
        "EXACT_SETTLED_REJECTION_REQUIRED_NO_CLEANUP")
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        rows = [dict(row) for row in connection.execute("SELECT * FROM receipts WHERE action_id=?", (ACTION,))]
        require(len(rows) == 1 and rows[0]["receipt_state"] == "rejected", "EXACT_REJECTED_RECEIPT_REQUIRED")
        payload = json.loads(rows[0]["payload_json"])
        require(isinstance(payload, dict) and payload.get("code") == "CONTROL_PLANE_APPROVED_PATCH_CONTRACT_MISMATCH",
            "REJECTION_CODE_CHANGED_REVIEW_REQUIRED")
        return {"receipt_id": rows[0]["receipt_id"], "code": payload["code"], "patch_or_proof_applied": False}
    finally:
        connection.close()


def observe():
    canary, common, pins, marker, database, family = observed_state()
    rejection = rejected_receipt(database, family) if family.get("receipt_states") == ["rejected"] else None
    verified = canary.verified_payload(family, marker, pins) if family.get("settled") and rejection is None else None
    return {"ok": True, "phase": "observe", "provenance": "central_mcp_service_trial",
        "family": canary.public_family(family), "verified_patch_and_initial_proof_summary": verified,
        "terminal_rejection": rejection, "native_semantic_acceptance": "pending",
        "acceptance_blocker": "NATIVE_CHATWEB_ACCEPTANCE_TRANSPORT_UNAVAILABLE",
        "replay_forbidden": True, "remote_mutation": False,
        "authority_context_preserved": True, "action_context_causally_verified": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("observe",))
    parser.parse_args()
    try:
        print(json.dumps(observe(), ensure_ascii=False, sort_keys=True))
    except Exception as error:
        print(json.dumps({"ok": False, "phase": "r11_observe_reconciliation_failed",
            "code": getattr(error, "code", "READ_ONLY_OBSERVATION_FAILED"), "remote_mutation": False,
            "replay_forbidden": True}, sort_keys=True))
        raise SystemExit(1) from None
