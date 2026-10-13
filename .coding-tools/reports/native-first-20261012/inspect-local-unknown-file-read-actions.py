"""Observe only selected UNKNOWN action correlations; never writes journals."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
REPOSITORY = Path(__file__).resolve().parents[3]
IDS = {
    "act_9db9b985a3d648b5b941f2e13a30ee47",
    "act_52409c69f1b84e08bb3fdd86747f79c3",
    "act_3849e259d55546639794cec40f63fea8",
}
FIELDS = {
    "schema_version", "operation_kind", "state", "action_id", "attempt_id", "receipt_state", "receipt_submitted",
    "command_id", "job_id", "status", "code", "diagnostic_code", "native_error_code", "job_lifecycle",
    "execution_started", "root_pid", "job_finished_at", "run_id", "wave_id", "tool_name", "operation",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def project(value):
    return {key: item for key, item in value.items() if key in FIELDS and not isinstance(item, (dict, list))}


def owner():
    value = json.loads((BASE / "recovery-host.json").read_text(encoding="utf-8-sig"))
    return {key: value.get(key) for key in ("owner_pid", "owner_process_start_token", "instance_id", "installation_id")}


def main():
    output = Path(__file__).with_name("local-unknown-file-read-action-evidence.json")
    if output.exists():
        raise RuntimeError("Preserve existing evidence")
    started = datetime.now(timezone.utc).isoformat()
    before = owner()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    journals = {}
    matches = []
    for file in BASE.glob("*journal*.json"):
        raw = file.read_bytes()
        journals[file.name] = {"sha256": sha(raw), "bytes": len(raw)}
        entries = json.loads(raw).get("entries", {})
        for entry in entries.values():
            if entry.get("action_id") in IDS:
                receipt = entry.get("receipt", {})
                payload = receipt.get("payload", {})
                matches.append({"journal": file.name, "entry": project(entry), "receipt": project(receipt), "payload": project(payload)})
    after_hashes = {name: sha((BASE / name).read_bytes()) for name in journals}
    stable = all(journals[name]["sha256"] == value for name, value in after_hashes.items())
    after = owner()
    reference = Path(__file__).with_name("production-transition-preflight-1791803582244.json")
    census = json.loads(reference.read_text(encoding="utf-8"))
    source = Path(__file__).with_name("r9e-installed-file-read-source-proof.json")
    report = {
        "schema_version": 1,
        "operation": "local_selected_unknown_file_read_action_evidence",
        "read_only": True,
        "observed_git_head": head,
        "capture_started_utc": started,
        "capture_finished_utc": datetime.now(timezone.utc).isoformat(),
        "production_identity_before": before,
        "production_identity_after": after,
        "production_identity_stable": before == after,
        "journals_observed": journals,
        "journal_bytes_stable_during_observation": stable,
        "selected_actions": matches,
        "selected_action_ids": sorted(IDS),
        "source_location_proof": {"path": str(source), "sha256": sha(source.read_bytes())},
        "canonical_idle_census_reference": {"path": str(reference), "sha256": sha(reference.read_bytes()),
            "observed_at": census["observed_at"], "local_live_work_idle": census["local_live_work_idle"], "counts": census["canonical_ledger_census"]["counts"]},
        "interpretation": "All three are preserved submitted UNKNOWN file-read receipts, diagnostic TARGET_MISSING; no command/job correlation in these receipts. Installed source proves this diagnostic is thrown before contents are read. No completion inferred or original receipt changed.",
        "limitations": ["Referenced idle census is an earlier observation and must be refreshed before lifecycle operations", "Supported append-only terminal reconciliation requires independent matching server attempt/receipt/source evidence"],
        "mutating_actions_performed": [],
    }
    report["ok"] = stable and before == after and len(matches) == 3 and {item["entry"]["action_id"] for item in matches} == IDS and all(item["receipt"].get("receipt_submitted") is True and item["receipt"].get("receipt_state") == "unknown" and item["payload"].get("diagnostic_code") == "CONTROL_PLANE_FILE_READ_TARGET_MISSING" for item in matches)
    with output.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
        target.write("\n")
    print(json.dumps({"ok": report["ok"], "report_path": str(output), "selected_actions": matches}, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
