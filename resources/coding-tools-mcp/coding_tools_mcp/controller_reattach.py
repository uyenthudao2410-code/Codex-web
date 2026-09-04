from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any


CONTROLLER_REATTACH_MAX_ACTIVE_RUNS = 32


def run_binding_from_metadata(metadata: dict[str, Any]) -> dict[str, Any] | None:
    resolution = metadata.get("problem_resolution")
    if not isinstance(resolution, dict) or resolution.get("work_origin") != "problem":
        return None
    problem_id = str(resolution.get("problem_id") or "").strip()
    revision = resolution.get("problem_revision")
    if not problem_id or isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        return None
    workspace_identity = metadata.get("workspace_identity")
    workspace_id = (
        str(workspace_identity.get("workspace_id") or "").strip()
        if isinstance(workspace_identity, dict)
        else ""
    )
    return {"workspace_id": workspace_id, "problem_id": problem_id, "problem_revision": revision}


def problem_event_revision_schema_active(connection: sqlite3.Connection) -> bool:
    columns = {
        str(column["name"])
        for column in connection.execute("PRAGMA table_info(problem_events)").fetchall()
    }
    return "problem_revision" in columns


def controller_identity(client: dict[str, Any], owner_client_id: str) -> dict[str, str] | None:
    if (
        str(client.get("client_type") or "") != "chatweb"
        or str(client.get("role") or "") != "controller"
        or not str(client.get("client_id") or "").strip()
    ):
        return None
    basis = {
        "client_id": str(client.get("client_id") or ""),
        "runtime_instance_id": str(client.get("runtime_instance_id") or ""),
        "session_instance": str(client.get("session_instance") or ""),
    }
    encoded = json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "controller_endpoint_id": "controller-" + hashlib.sha256(encoded).hexdigest()[:40],
        "owner_client_id": owner_client_id,
    }


def attachment_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "workspace_id": str(row["workspace_id"]),
        "problem_id": str(row["problem_id"]),
        "problem_revision": int(row["problem_revision"]),
        "generation": int(row["generation"]),
        "controller_endpoint_id": str(row["controller_endpoint_id"]),
        "owner_client_id": str(row["owner_client_id"]),
        "last_reattach_id": str(row["last_reattach_id"]),
        "updated_at": str(row["updated_at"]),
    }


def reattach_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "reattach_id": str(row["reattach_id"]),
        "workspace_id": str(row["workspace_id"]),
        "problem_id": str(row["problem_id"]),
        "problem_revision": int(row["problem_revision"]),
        "prior_generation": int(row["prior_generation"]),
        "generation": int(row["generation"]),
        "controller_endpoint_id": str(row["controller_endpoint_id"]),
        "owner_client_id": str(row["owner_client_id"]),
        "ack_id": str(row["ack_id"]),
        "ack_status": str(row["ack_status"]),
        "continuity_core_fingerprint": str(row["continuity_core_fingerprint"]),
        "active_run_transfers": json.loads(str(row["active_run_transfers_json"] or "[]")),
        "source_fingerprint": str(row["source_fingerprint"]),
        "runtime_behavior_fingerprint": str(row["runtime_behavior_fingerprint"]),
        "created_at": str(row["created_at"]),
    }


def ensure_controller_reattach_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS controller_goal_attachments (
            workspace_id TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
            generation INTEGER NOT NULL CHECK(generation>=1),
            controller_endpoint_id TEXT NOT NULL,
            owner_client_id TEXT NOT NULL,
            last_reattach_id TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(workspace_id,problem_id),
            FOREIGN KEY(problem_id,problem_revision)
                REFERENCES problem_revisions(problem_id,revision) ON DELETE RESTRICT,
            FOREIGN KEY(owner_client_id)
                REFERENCES hub_clients(client_id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS controller_reattach_receipts (
            reattach_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
            prior_generation INTEGER NOT NULL CHECK(prior_generation>=0),
            generation INTEGER NOT NULL CHECK(generation>=1),
            controller_endpoint_id TEXT NOT NULL,
            owner_client_id TEXT NOT NULL,
            ack_id TEXT NOT NULL,
            ack_status TEXT NOT NULL,
            continuity_core_fingerprint TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            active_run_transfers_json TEXT NOT NULL DEFAULT '[]',
            source_fingerprint TEXT NOT NULL,
            runtime_behavior_fingerprint TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(problem_id,problem_revision)
                REFERENCES problem_revisions(problem_id,revision) ON DELETE RESTRICT,
            FOREIGN KEY(ack_id)
                REFERENCES controller_knowledge_acks(ack_id) ON DELETE RESTRICT,
            FOREIGN KEY(owner_client_id)
                REFERENCES hub_clients(client_id) ON DELETE RESTRICT
        );
        CREATE INDEX IF NOT EXISTS idx_controller_reattach_problem_generation
            ON controller_reattach_receipts(workspace_id,problem_id,generation DESC);
        """
    )
