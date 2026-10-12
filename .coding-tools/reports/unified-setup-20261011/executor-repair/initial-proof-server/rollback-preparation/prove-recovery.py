"""Focused, local-only proof using frozen Store395 and r11 source modules."""
from __future__ import annotations

import base64
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zlib

OUT = Path(__file__).resolve().parent
PARENT = OUT.parent
BASE_REVISION = "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
R11_REVISION = "9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c"
BASE = PARENT.parent / "store-delta" / ("codex-control-plane-" + BASE_REVISION)
R11 = PARENT / ("codex-control-plane-" + R11_REVISION)
MANIFEST = json.loads((OUT / "packet-manifest.json").read_text())
RECOVERY = OUT / MANIFEST["release_name"]
NOW = 1_700_000_000_000
OWNER, DEVICE = "owner-default", "recovery-fixture-node"
CONTRACT = {"schema_version": 32, "profile": "workspace_context", "sha256": "c" * 64}
PLAN = {"argv": ["node", "--test", "tests/fixture.test.js"], "cwd": "", "timeout_ms": 60000, "max_output_bytes": 32768}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(name, root):
    path = root / "control-plane/control_plane/store.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def snapshot(path):
    with closing(sqlite3.connect(path)) as con:
        schema = con.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
        tables = [r[1] for r in schema if r[0] == "table"]
        values = {t: con.execute(f'SELECT * FROM "{t}" ORDER BY rowid').fetchall() for t in tables}
        columns = {t: con.execute(f'PRAGMA table_info("{t}")').fetchall() for t in tables}
        return {"user_version": con.execute("PRAGMA user_version").fetchone()[0], "schema": schema, "columns": columns, "rows": values}

def fingerprint(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())

def patch(path="src/fixture.txt"):
    content = b"updated fixture\n"
    envelope = "\n".join(("*** Begin Patch", "*** Write Exact File: " + path,
        "@@ encoding=zlib-base64 preimage_sha256=" + "a" * 64 + " postimage_sha256=" + sha(content),
        "+" + base64.b64encode(zlib.compress(content)).decode(), "*** End Patch", ""))
    return envelope

def queue_reviewed(store, principal, binding, key, *, verification=None):
    envelope = patch()
    arguments = dict(owner_id=OWNER, principal_id=principal, binding_id=binding, path="src/fixture.txt",
                     preimage_sha256="a" * 64, patch_sha256=sha(envelope.encode()), validation_profile="targeted",
                     idempotency_key=key + "-permission", facade_contract=CONTRACT)
    if verification is not None:
        arguments["verification"] = verification
    permission = store.request_mcp_patch_permission(**arguments)
    store.approve_mcp_permission_request(owner_id=OWNER, permission_request_id=permission["permission_request_id"])
    action_args = dict(owner_id=OWNER, principal_id=principal, permission_request_id=permission["permission_request_id"],
                       patch_envelope=envelope, idempotency_key=key + "-action", facade_contract=CONTRACT)
    if verification is not None:
        action_args["verification"] = verification
    return store.request_mcp_approved_patch(**action_args)

def complete(store, action_id, *, verified=False):
    delivery = next(d for d in store.poll_actions(device_id=DEVICE, lane="approved_patch") if d["action_id"] == action_id)
    payload = {"fixture_only": True, "run_id": "a" * 32, "wave_id": "b" * 32}
    if verified:
        payload["initial_verification"] = {"plan_sha256": fingerprint(PLAN), "proof_status": "failed", "proof_ids": [], "proof_fingerprint": None}
    kwargs = dict(device_id=DEVICE, action_id=action_id, attempt_id=delivery["attempt_id"],
                  receipt_state="completed", local_handle="fixture-local-handle-" + action_id, payload=payload)
    store.record_receipt(**kwargs)
    return kwargs

def expect_denied(operation, error):
    try:
        operation()
    except error:
        return
    raise AssertionError("guard did not deny operation")

def main():
    assert not (OUT / "proof-receipt.json").exists(), "immutable proof receipt already exists"
    baseline, r11, recovery = load("frozen_schema28_store", BASE), load("frozen_schema29_store", R11), load("recovery_schema29_store", RECOVERY)
    checks = []
    with tempfile.TemporaryDirectory(prefix="schema29-recovery-proof-") as temp:
        path = Path(temp) / "fixture.sqlite3"
        store28 = baseline.ControlPlaneStore(path, clock=lambda: NOW)
        store28.enroll_node(owner_id=OWNER, device_id=DEVICE, endpoint_id="recovery-fixture-endpoint", display_name="Recovery fixture")
        store28.register_node_workspace(device_id=DEVICE, workspace_id="recovery-fixture-workspace", workspace_generation="recovery-fixture-generation",
                                         display_name="Recovery fixture", capabilities={"read": True, "write": True, "exec": True})
        binding = store28.create_binding(owner_id=OWNER, device_id=DEVICE, workspace_id="recovery-fixture-workspace",
                                         workspace_generation="recovery-fixture-generation", display_name="Recovery fixture")["binding_id"]
        principal = store28.link_oauth_principal(owner_id=OWNER, issuer="https://identity.example.test/recovery", subject="recovery-fixture-subject")["principal_id"]
        store28.heartbeat(device_id=DEVICE, endpoint_id="recovery-fixture-endpoint", runtime_instance_id="recovery-fixture-runtime",
                           mcp_server_instance_id="recovery-fixture-mcp", activation_epoch="recovery-fixture-epoch", contract_version="sha256:" + "c" * 64, readiness="ready")
        legacy = queue_reviewed(store28, principal, binding, "legacy-recovery")
        legacy_receipt = complete(store28, legacy["action_id"])
        before_migration = snapshot(path)
        store29 = r11.ControlPlaneStore(path, clock=lambda: NOW)
        after_migration = snapshot(path)
        for table, oldrows in before_migration["rows"].items():
            if table in {"mcp_permission_requests", "mcp_approved_patch_intents", "mcp_standing_patch_intents"}:
                cols = [c[1] for c in before_migration["columns"][table]]
                with closing(sqlite3.connect(path)) as con:
                    assert con.execute(f"SELECT {','.join(cols)} FROM {table} ORDER BY rowid").fetchall() == oldrows
            else:
                assert after_migration["rows"][table] == oldrows
        assert after_migration["user_version"] == 29
        checks.append("schema28_to29_preserves_all_existing_rows")
        verified = queue_reviewed(store29, principal, binding, "verified-recovery", verification=PLAN)
        verified_receipt = complete(store29, verified["action_id"], verified=True)
        task = store29.create_mcp_task_session(owner_id=OWNER, principal_id=principal, binding_id=binding,
                                               label="Recovery verification", idempotency_key="recovery-fixture-task-key")
        store29.claim_mcp_task_writer_lease(owner_id=OWNER, principal_id=principal, task_id=task["task_id"])
        envelope = patch()
        queued = store29.request_mcp_standing_patch(owner_id=OWNER, principal_id=principal, binding_id=binding,
            path="src/fixture.txt", preimage_sha256="a" * 64, patch_sha256=sha(envelope.encode()), validation_profile="targeted",
            patch_envelope=envelope, idempotency_key="queued-verification-recovery", facade_contract=CONTRACT, task_id=task["task_id"], verification=PLAN)
        store29.set_admission_mode(mode="recovery")
        before = snapshot(path)
        closed = recovery.ControlPlaneStore(path, clock=lambda: NOW)
        assert closed.health()["schema_version"] == 29 and closed.admission_status()["admission_mode"] == "recovery"
        assert snapshot(path) == before
        checks.append("recovery_open_preserves_every_row_column_schema_and_history")
        for table in ("mcp_permission_requests", "mcp_approved_patch_intents", "mcp_standing_patch_intents"):
            with closing(sqlite3.connect(path)) as con:
                assert con.execute(f"SELECT COUNT(*) FROM {table} WHERE verification_json IS NOT NULL").fetchone()[0] >= 1
        checks.append("postmigration_verification_json_preserved_in_all_three_tables")
        for lane in (None, "generic", "read_only_workspace_context", "bounded_file_read", "approved_patch", "bounded_exec", "bounded_artifact", "document_write"):
            assert closed.poll_actions(device_id=DEVICE, lane=lane) == []
        assert closed.action(owner_id=OWNER, action_id=queued["action_id"])["delivery_state"] == "queued"
        assert closed.record_receipt(**legacy_receipt)["replayed"]
        assert closed.record_receipt(**verified_receipt)["replayed"]
        assert closed.action_observation(owner_id=OWNER, action_id=verified["action_id"])["receipts"]
        checks.append("no_dispatch_or_new_attempt_and_existing_receipt_replay_remains_idempotent")
        for mode in ("open", "scoped_pilot", "recovery"):
            expect_denied(lambda mode=mode: closed.set_admission_mode(mode=mode), recovery.ConflictError)
        for name in MANIFEST["denied_store_entry_points"]:
            method = getattr(closed, name)
            kwargs = {key: "fixture-argument" for key, parameter in inspect.signature(method).parameters.items() if parameter.default is inspect.Parameter.empty}
            expect_denied(lambda method=method, kwargs=kwargs: method(**kwargs), recovery.ConflictError)
        expect_denied(lambda: closed.request_mcp_patch_permission(owner_id=OWNER, principal_id=principal, binding_id=binding, path="src/other.txt",
            preimage_sha256="a" * 64, patch_sha256="b" * 64, validation_profile="targeted", idempotency_key="new-intake-prohibited-key", facade_contract=CONTRACT), recovery.ConflictError)
        assert snapshot(path) == before
        checks.append("new_intake_authority_grants_context_pilot_and_legacy_acceptance_denied_without_history_change")
        # A direct external state change must not bypass fail-closed intake/dispatch.
        with closing(sqlite3.connect(path)) as con:
            con.execute("UPDATE control_plane_state SET state_value='open' WHERE state_key='admission_mode'")
            con.commit()
        drift = snapshot(path)
        assert closed.poll_actions(device_id=DEVICE, lane="approved_patch") == []
        expect_denied(lambda: closed.request_mcp_patch_permission(owner_id=OWNER, principal_id=principal, binding_id=binding, path="src/other.txt",
            preimage_sha256="a" * 64, patch_sha256="b" * 64, validation_profile="targeted", idempotency_key="drift-intake-prohibited-key", facade_contract=CONTRACT), recovery.ConflictError)
        expect_denied(lambda: recovery.ControlPlaneStore(path, clock=lambda: NOW), RuntimeError)
        assert snapshot(path) == drift
        checks.append("admission_drift_does_not_enable_intake_dispatch_or_restart")
        # Negative startup cases use independent copies, retaining the original fixture.
        for version in (28, 30):
            candidate = Path(temp) / f"schema{version}.sqlite3"
            with closing(sqlite3.connect(path)) as src, closing(sqlite3.connect(candidate)) as dst:
                src.backup(dst)
            with closing(sqlite3.connect(candidate)) as con:
                con.execute(f"PRAGMA user_version={version}")
                con.commit()
            snap = snapshot(candidate)
            expect_denied(lambda: recovery.ControlPlaneStore(candidate, clock=lambda: NOW), RuntimeError)
            assert snapshot(candidate) == snap
        fresh = Path(temp) / "missing.sqlite3"
        expect_denied(lambda: recovery.ControlPlaneStore(fresh), RuntimeError)
        assert not fresh.exists()
        checks.append("fresh_older_newer_or_open_database_refused_without_migration_or_restore")
        counts = {table: len(rows) for table, rows in before["rows"].items()}
        preserved_digest = fingerprint(before)
    receipt = {"operation": "local_schema29_closed_recovery_proof", "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "recovery_source_revision": MANIFEST["source_revision"], "recovery_package_source_sha256": MANIFEST["package_source_sha256"],
        "baseline_schema28_source_revision": BASE_REVISION, "migration_schema29_source_revision": R11_REVISION,
        "proof_script_sha256": sha(Path(__file__).read_bytes()), "checks_passed": checks, "check_count": len(checks),
        "preserved_database_snapshot_sha256": preserved_digest, "preserved_table_row_counts": counts,
        "fixture_credentials": "generated local test data; values neither retained nor printed", "temporary_database_retained": False,
        "network_or_ssh_used": False, "deployment_performed": False, "service_operation_performed": False,
        "authority_renewal_performed": False, "windows_runtime_touched": False}
    with (OUT / "proof-receipt.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"checks_passed": checks, "check_count": len(checks), "source_revision": MANIFEST["source_revision"], "preserved_database_snapshot_sha256": preserved_digest}, sort_keys=True))

if __name__ == "__main__":
    main()
