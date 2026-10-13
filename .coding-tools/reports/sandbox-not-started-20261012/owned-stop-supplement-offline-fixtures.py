"""Exercise supplementary observation with replaced live boundaries only."""
import ast
import contextlib
import copy
import importlib.util
import io
import json
import time
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observe-original-owned-stop-readonly.py"
spec = importlib.util.spec_from_file_location("supplement_fixture_subject", SOURCE)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
ast.parse(SOURCE.read_text(encoding="utf-8"))
m = s.m
attempt = "b18bb16d623240db9d014361770302db"
paths = {name: HERE / ("owned-stop-" + name + "-" + attempt + ".json") for name in ("dispatch", "plan", "unknown")}
documents = {name: m.read_json(path) for name, path in paths.items()}
bound = documents["plan"]["binding"]
record = {"sandbox_id": bound["backend"]["sandbox_id"], "state": "stopped",
          "mapped_folders": [{"host": str(m.ROOT), "sandbox": "C:/fixture", "read_only": False}]}
argv = [str(SOURCE)]
for name, path in paths.items():
    argv.extend(["--" + name, str(path), "--" + name + "-sha256", m.file_sha(path)])
argv.extend(["--package-proof", str(HERE / "fixture-manifest.json"), "--observation-id", "c" * 32])
argv.extend(["--current-writer-generation", "2"])
passed = []

def case(label, hosts, expected_ok=None, expected_error=None, changed_mapping=False, changed_native_after=False):
    r = copy.deepcopy(record)
    if changed_mapping: r["mapped_folders"][0]["host"] = "E:/foreign-workspace"
    expected_digest = bound["backend"]["mapped_folders_sha256"]
    original_digest = m.digest
    def fixture_digest(value):
        if value == record["mapped_folders"]: return expected_digest
        return original_digest(value)
    def fixture_json(path):
        for name, p in paths.items():
            if path == p: return copy.deepcopy(documents[name])
        assert path == Path(bound["backend"]["record_path"])
        return copy.deepcopy(r)
    output = io.StringIO()
    native_results = [bound["native_warm_job"], {} if changed_native_after else bound["native_warm_job"]]
    with patch.object(s, "__file__", str(SOURCE)), patch.object(__import__("sys"), "argv", argv), patch.object(m, "read_json", side_effect=fixture_json), patch.object(m, "digest", side_effect=fixture_digest), patch.object(m, "package_facts", return_value=bound["package"]), patch.object(m, "runtime_facts", return_value=bound["runtime"]), patch.object(m, "warm_receipt_facts", return_value=bound["warm_receipt"]), patch.object(m, "native_job_facts", side_effect=native_results), patch.object(s, "central_authority", return_value={"current_writer": {"lease_generation": 2}}), patch.object(s, "host_inventory", return_value=hosts), patch.object(s.time, "sleep") as sleeper, patch.object(m, "write_new", return_value={"path": "offline-fixture-no-write", "sha256": "d" * 64}), patch.object(m, "file_sha", side_effect=lambda path: "e" * 64 if path == Path(bound["backend"]["record_path"]) else __import__("hashlib").sha256(path.read_bytes()).hexdigest()), contextlib.redirect_stdout(output):
        try:
            s.main()
        except RuntimeError as error:
            assert expected_error == str(error), (label, str(error))
        else:
            assert expected_error is None, label
            result = json.loads(output.getvalue())
            assert result["ok"] is expected_ok
            assert result["observed"]["kernel_memory_process_count"] == len(hosts["kernel_memory_observations"])
            assert result["observation_state"] == ("verified_owned_hosts_absent" if expected_ok else "owned_host_shutdown_pending")
            if not hosts["user_mode_hosts"]: sleeper.assert_called_once_with(5)
            else: sleeper.assert_not_called()
    passed.append(label)

empty = {"user_mode_hosts": [], "kernel_memory_observations": []}
case("Complete absence accepted without stop replay", empty, True)
case("Kernel aggregate remaining is observational and does not reject owned host absence", {"user_mode_hosts": [], "kernel_memory_observations": [{"pid": 28056, "ownership_inferred": False}]}, True)
case("User-mode host remaining reports shutdown pending", {"user_mode_hosts": [{"pid": 3492}], "kernel_memory_observations": []}, False)
case("Changed mapping rejected", empty, expected_error="ORIGINAL_STOP_MAPPING_OR_DAEMON_ABSENCE_NOT_CONFIRMED", changed_mapping=True)
case("New or changed native Job after cooldown rejected", empty, expected_error="ORIGINAL_POST_STOP_STATE_CHANGED_DURING_OBSERVATION", changed_native_after=True)
def authority_case(label, mutate=None, expected_error=None):
    observed = copy.deepcopy(bound["central"])
    observed["writer"].update(lease_generation=2, expires_at_ms=int(time.time() * 1000) + 60000)
    observed["writer"].pop("fresh_unexpired_observed", None)
    observed["node"]["last_seen_at_ms"] = int(time.time() * 1000)
    if mutate: mutate(observed)
    args = __import__("types").SimpleNamespace(warm_action_id=bound["warm_receipt"]["action_id"], canary_task_id=bound["warm_receipt"]["task_id"])
    result = __import__("types").SimpleNamespace(returncode=0, stdout=json.dumps(observed))
    with patch.object(s.subprocess, "run", return_value=result):
        try: authority = s.central_authority(args, bound["central"], 2)
        except RuntimeError as error: assert expected_error == str(error), (label, str(error))
        else:
            assert expected_error is None
            assert authority["original_writer_generation"] == 1 and authority["current_writer"]["lease_generation"] == 2
    passed.append(label)
authority_case("Original generation one remains immutable while renewed current generation two accepted")
authority_case("Changed original intent generation rejected", lambda d: d["intent"].update(writer_lease_generation=2), "ORIGINAL_COLD_WARM_GENERATION_ONE_LINEAGE_CHANGED")
authority_case("Expired renewed writer rejected", lambda d: d["writer"].update(expires_at_ms=0), "EXACT_RENEWED_CURRENT_GENERATION_TWO_AUTHORITY_NOT_FRESH")
authority_case("Released renewed writer rejected", lambda d: d["writer"].update(released_at_ms=1), "EXACT_RENEWED_CURRENT_GENERATION_TWO_AUTHORITY_NOT_FRESH")
authority_case("Different current generation rejected", lambda d: d["writer"].update(lease_generation=3), "EXACT_RENEWED_CURRENT_GENERATION_TWO_AUTHORITY_NOT_FRESH")
authority_case("Changed original action settlement rejected", lambda d: d["action"].update(delivery_state="pending"), "ORIGINAL_COLD_WARM_GENERATION_ONE_LINEAGE_CHANGED")
receipt = {"schema_version": 1, "operation": "original_stop_supplement_offline_validation",
           "producer_sha256": m.file_sha(SOURCE), "ast_parse": "PASS", "cases_passed": len(passed),
           "cases": passed, "live_boundary_functions_replaced": True,
           "stop_effect_performed": False, "network_requests_performed": False,
           "database_mutated": False, "node_journal_modified": False}
saved = m.write_new(HERE / "owned-stop-supplement-host-boundary-final-validation.json", receipt)
print(json.dumps({"ok": True, "cases_passed": len(passed), "producer_sha256": receipt["producer_sha256"], **saved}))
