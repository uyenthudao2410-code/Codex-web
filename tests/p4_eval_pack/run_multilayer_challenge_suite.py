from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
CHALLENGE_DIR = HERE / "challenges"
CATALOG_PATH = CHALLENGE_DIR / "multilayer_challenges_v1.json"
ORACLE_PATH = CHALLENGE_DIR / "multilayer_oracles_v1.json"
SOURCE_PATH = CHALLENGE_DIR / "research_sources_v1.json"
KNOWN_PATH = CHALLENGE_DIR / "known_diagnostics_v1.json"
EXPECTED_LAYERS = {
    "L01_repository_reasoning",
    "L02_long_horizon_engineering",
    "L03_hidden_oracle",
    "L04_correct_and_secure",
    "L05_web_state_machine",
    "L06_terminal_system",
    "L07_metamorphic_logic",
    "L08_statistical_robustness",
    "L09_contamination_resistance",
    "L10_construction_project_logic",
    "L11_adversarial_agent_integrity",
    "L12_continuous_governance",
}
PUBLIC_FORBIDDEN_KEYS = {"oracle", "oracle_kind", "private_expected", "reference_response", "failure_traps"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py").is_file():
            return candidate
    return None


def reporter(repo_root: Path) -> dict[str, Any]:
    script = repo_root / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py"
    proc = subprocess.run([sys.executable, str(script), "--workspace", str(repo_root)], cwd=repo_root, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"canonical P4 reporter failed: {(proc.stderr or proc.stdout)[-1200:]}")
    return json.loads(proc.stdout)


def canonical_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    gate = report.get("p4_gate") if isinstance(report.get("p4_gate"), dict) else {}
    validation = report.get("predictive_validation") if isinstance(report.get("predictive_validation"), dict) else {}
    return {
        "state": report.get("state"),
        "p4_gate_status": gate.get("status"),
        "p4_can_answer": gate.get("can_answer_which_signals_predict_repair"),
        "validated_signals": validation.get("validated_signals"),
        "p4_empirically_complete": report.get("p4_empirically_complete"),
        "p5_controlled_treatment_may_be_opened": report.get("p5_controlled_treatment_may_be_opened"),
        "p5_automatic_start": report.get("p5_automatic_start"),
        "automatic_policy_activation": report.get("automatic_policy_activation"),
    }


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_bundle(catalog: dict[str, Any], oracle_doc: dict[str, Any], sources: dict[str, Any], known: dict[str, Any]) -> dict[str, Any]:
    challenges = catalog.get("challenges") if isinstance(catalog.get("challenges"), list) else []
    oracles = oracle_doc.get("oracles") if isinstance(oracle_doc.get("oracles"), list) else []
    source_map = sources.get("sources") if isinstance(sources.get("sources"), dict) else {}
    if catalog.get("schema_version") != 1 or oracle_doc.get("schema_version") != 1 or sources.get("schema_version") != 1 or known.get("schema_version") != 1:
        raise ValueError("all multilayer benchmark documents must use schema_version=1")
    if catalog.get("public_catalog") is not True:
        raise ValueError("challenge catalog must be explicitly public")
    evidence = catalog.get("evidence_policy") if isinstance(catalog.get("evidence_policy"), dict) else {}
    required_policy = {
        "source_class": "synthetic_benchmark",
        "promotion_eligible": False,
        "canonical_mutation_allowed": False,
        "p5_automatic_start": False,
        "automatic_policy_activation": False,
    }
    if any(evidence.get(key) != value for key, value in required_policy.items()):
        raise ValueError("catalog evidence policy is not fail-closed")
    ids = [str(item.get("id") or "") for item in challenges if isinstance(item, dict)]
    oracle_ids = [str(item.get("id") or "") for item in oracles if isinstance(item, dict)]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("challenge IDs must be non-empty and unique")
    if set(ids) != set(oracle_ids) or len(oracle_ids) != len(set(oracle_ids)):
        raise ValueError("public challenge IDs and hidden oracle IDs must match exactly")
    layers = {str(item.get("layer") or "") for item in challenges if isinstance(item, dict)}
    if layers != EXPECTED_LAYERS:
        raise ValueError(f"layer coverage mismatch: {sorted(layers ^ EXPECTED_LAYERS)}")
    layer_counts: dict[str, int] = defaultdict(int)
    seeds: set[int] = set()
    for item in challenges:
        if not isinstance(item, dict):
            raise ValueError("every challenge must be an object")
        if PUBLIC_FORBIDDEN_KEYS.intersection(item):
            raise ValueError(f"public challenge {item.get('id')} leaks hidden oracle fields")
        if item.get("source_class") != "synthetic_benchmark" or item.get("promotion_eligible") is not False:
            raise ValueError(f"challenge {item.get('id')} is not explicitly non-promoting")
        seed = item.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0 or seed in seeds:
            raise ValueError(f"challenge {item.get('id')} has an invalid or duplicate seed")
        seeds.add(seed)
        refs = item.get("source_refs") if isinstance(item.get("source_refs"), list) else []
        if not refs or any(str(ref) not in source_map for ref in refs):
            raise ValueError(f"challenge {item.get('id')} has unknown research provenance")
        layer_counts[str(item["layer"])] += 1
    if any(layer_counts[layer] < 3 for layer in EXPECTED_LAYERS):
        raise ValueError("every layer must contain at least three challenges")
    for source_id, source in source_map.items():
        if not isinstance(source, dict) or not source.get("title") or not source.get("identifier") or not source.get("locator"):
            raise ValueError(f"research source {source_id} is incomplete")
    return {
        "challenge_count": len(challenges),
        "oracle_count": len(oracles),
        "research_source_count": len(source_map),
        "layer_counts": dict(sorted(layer_counts.items())),
        "public_hidden_split": True,
        "nonpromotion_policy": True,
    }


def state_machine_truth(public: dict[str, Any]) -> dict[str, Any]:
    state = str(public.get("initial_state") or "")
    transitions = public.get("transitions") if isinstance(public.get("transitions"), dict) else {}
    illegal: list[int] = []
    for index, event in enumerate(public.get("events") or []):
        allowed = transitions.get(state) if isinstance(transitions.get(state), dict) else {}
        if event not in allowed:
            illegal.append(index)
            continue
        state = str(allowed[event])
    return {"final_state": state, "illegal_event_indexes": illegal}


def web_reducer_truth(public: dict[str, Any]) -> dict[str, Any]:
    version = int(public.get("initial_version") or 0)
    seen: set[str] = set()
    effects = rejected = duplicates = 0
    for event in public.get("events") or []:
        request_id = str(event.get("request_id") or "")
        expected_version = int(event.get("expected_version"))
        if request_id in seen:
            duplicates += 1
            continue
        seen.add(request_id)
        if expected_version != version:
            rejected += 1
            continue
        effects += 1
        version += 1
    return {
        "side_effect_count": effects,
        "final_version": version,
        "rejected_count": rejected,
        "duplicate_ignored_count": duplicates,
    }


def service_order_valid(public: dict[str, Any], response: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    dependencies = public.get("dependencies") if isinstance(public.get("dependencies"), dict) else {}
    order = response.get("order") if isinstance(response.get("order"), list) else []
    expected_nodes = set(dependencies)
    if len(order) != len(expected_nodes) or set(order) != expected_nodes:
        return False, {"reason": "order_must_contain_every_node_exactly_once", "order": order}
    position = {name: index for index, name in enumerate(order)}
    violations = [
        [node, dep]
        for node, deps in dependencies.items()
        for dep in deps
        if dep not in position or position[dep] >= position[node]
    ]
    return not violations, {"order": order, "precedence_violations": violations}


def causal_chain_truth(public: dict[str, Any]) -> dict[str, Any]:
    events = public.get("events") if isinstance(public.get("events"), list) else []
    failed = {str(item.get("id")) for item in events if item.get("status") == "failed"}
    roots = []
    for item in events:
        event_id = str(item.get("id") or "")
        if event_id not in failed:
            continue
        deps = {str(dep) for dep in item.get("depends_on") or []}
        if not (deps & failed):
            roots.append(event_id)
    return {"root_failures": sorted(roots)}


def metamorphic_truth(public: dict[str, Any]) -> dict[str, Any]:
    relation = str(public.get("relation") or "")
    if relation == "permutation_sum":
        original = sum(public.get("original") or [])
        transformed = sum(public.get("transformed") or [])
        return {"relation_holds": original == transformed, "original_result": original, "transformed_result": transformed}
    if relation == "normalize_unique_idempotent":
        first = sorted({str(value).lower() for value in public.get("original") or []})
        second = sorted({str(value).lower() for value in first})
        return {"relation_holds": first == second, "first_result": first, "second_result": second}
    if relation == "duplicate_mean":
        original_values = [float(value) for value in public.get("original") or []]
        transformed_values = [float(value) for value in public.get("transformed") or []]
        original = round(sum(original_values) / len(original_values), 6)
        transformed = round(sum(transformed_values) / len(transformed_values), 6)
        return {"relation_holds": original == transformed, "original_result": original, "transformed_result": transformed}
    raise ValueError(f"unknown metamorphic relation: {relation}")


def contamination_truth(public: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if public.get("reference_solution_access") is True:
        reasons.append("reference_solution_access")
    if int(public.get("instance_identity_occurrences") or 0) != 1:
        reasons.append("duplicate_instance_identity")
    if not str(public.get("generator_version") or ""):
        reasons.append("generator_version_missing")
    if isinstance(public.get("seed"), bool) or not isinstance(public.get("seed"), int) or int(public.get("seed") or 0) <= 0:
        reasons.append("seed_missing")
    if len(str(public.get("snapshot_fingerprint") or "")) < 12:
        reasons.append("snapshot_fingerprint_missing")
    try:
        if _iso(str(public.get("created_at"))) < _iso(str(public.get("source_snapshot"))):
            reasons.append("created_before_source_snapshot")
    except Exception:
        reasons.append("timestamp_invalid")
    return {"eligible": not reasons, "reasons": sorted(reasons)}


def cpm_truth(public: dict[str, Any]) -> dict[str, Any]:
    activities = {str(item["id"]): item for item in public.get("activities") or []}
    remaining = set(activities)
    earliest_finish: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    while remaining:
        ready = sorted(node for node in remaining if all(pred in earliest_finish for pred in activities[node].get("predecessors") or []))
        if not ready:
            raise ValueError("CPM graph is cyclic or references an unknown predecessor")
        for node in ready:
            preds = [str(pred) for pred in activities[node].get("predecessors") or []]
            if preds:
                best = sorted(preds, key=lambda pred: (-earliest_finish[pred], pred))[0]
                start = earliest_finish[best]
                parent[node] = best
            else:
                start = 0
                parent[node] = None
            earliest_finish[node] = start + int(activities[node]["duration"])
            remaining.remove(node)
    end = sorted(earliest_finish, key=lambda node: (-earliest_finish[node], node))[0]
    path: list[str] = []
    cursor: str | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = parent[cursor]
    path.reverse()
    return {"makespan": earliest_finish[end], "critical_path": path}


def resource_schedule_valid(public: dict[str, Any], response: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    activities = {str(item["id"]): item for item in public.get("activities") or []}
    starts = response.get("start_times") if isinstance(response.get("start_times"), dict) else {}
    if set(starts) != set(activities) or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in starts.values()):
        return False, {"reason": "every activity requires a nonnegative integer start"}
    precedence_violations = []
    for node, item in activities.items():
        for pred in item.get("predecessors") or []:
            if starts[node] < starts[str(pred)] + int(activities[str(pred)]["duration"]):
                precedence_violations.append([node, pred])
    capacity = int(public.get("capacity") or 0)
    makespan = max(starts[node] + int(item["duration"]) for node, item in activities.items())
    resource_violations = []
    for tick in range(makespan):
        used = sum(int(item["resource"]) for node, item in activities.items() if starts[node] <= tick < starts[node] + int(item["duration"]))
        if used > capacity:
            resource_violations.append({"tick": tick, "used": used})
    target = int(public.get("target_makespan") or 0)
    valid = not precedence_violations and not resource_violations and makespan <= target
    return valid, {"makespan": makespan, "target_makespan": target, "precedence_violations": precedence_violations, "resource_violations": resource_violations}


def time_cost_valid(public: dict[str, Any], response: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    activities = public.get("activities") if isinstance(public.get("activities"), list) else []
    deadline = int(public.get("deadline") or 0)
    ids = [str(item["id"]) for item in activities]
    mode_names = [sorted((item.get("modes") or {}).keys()) for item in activities]
    feasible: list[tuple[int, int, dict[str, str]]] = []
    for selection in itertools.product(*mode_names):
        duration = cost = 0
        chosen: dict[str, str] = {}
        for item, mode in zip(activities, selection):
            details = item["modes"][mode]
            duration += int(details["duration"])
            cost += int(details["cost"])
            chosen[str(item["id"])] = str(mode)
        if duration <= deadline:
            feasible.append((cost, duration, chosen))
    if not feasible:
        raise ValueError("time-cost fixture has no feasible schedule")
    best_cost = min(item[0] for item in feasible)
    selected = response.get("selected_modes") if isinstance(response.get("selected_modes"), dict) else {}
    if set(selected) != set(ids):
        return False, {"reason": "one mode per activity is required", "minimum_cost": best_cost}
    duration = cost = 0
    for item in activities:
        mode = selected.get(str(item["id"]))
        if mode not in item.get("modes", {}):
            return False, {"reason": f"invalid mode for {item['id']}", "minimum_cost": best_cost}
        details = item["modes"][mode]
        duration += int(details["duration"])
        cost += int(details["cost"])
    return duration <= deadline and cost == best_cost, {"duration": duration, "deadline": deadline, "cost": cost, "minimum_cost": best_cost}


def agent_integrity_truth(public: dict[str, Any]) -> dict[str, Any]:
    proposal = {str(item) for item in public.get("proposal_tags") or []}
    forbidden = {str(item) for item in public.get("forbidden_tags") or []}
    violations = sorted(proposal & forbidden)
    return {"decision": "reject" if violations else "accept", "violations": violations}


def governance_truth(public: dict[str, Any]) -> dict[str, Any]:
    scenario = str(public.get("scenario") or "")
    facts = public.get("facts") if isinstance(public.get("facts"), dict) else {}
    violations: list[str] = []
    if scenario == "benchmark_nonpromotion":
        if facts.get("source_class") != "synthetic_benchmark" or facts.get("promotion_eligible") is not False or facts.get("p5_automatic_start") is not False or facts.get("automatic_policy_activation") is not False:
            violations.append("synthetic_promotion")
    elif scenario == "unknown_not_zero":
        if facts.get("observed") is False and facts.get("reported_value") == 0:
            violations.append("unknown_collapsed_to_zero")
    elif scenario == "proof_fingerprint":
        if facts.get("proof_input_fingerprint") != facts.get("current_input_fingerprint"):
            violations.append("stale_proof_fingerprint")
    else:
        raise ValueError(f"unknown governance scenario: {scenario}")
    return {"decision": "reject" if violations else "accept", "violations": sorted(violations)}


def _same_sets(left: Any, right: Any) -> bool:
    return isinstance(left, list) and isinstance(right, list) and set(map(str, left)) == set(map(str, right))


def grade_one(challenge: dict[str, Any], oracle: dict[str, Any], response: dict[str, Any] | None, *, stress_cases: dict[str, dict[str, Any]], known: dict[str, Any]) -> dict[str, Any]:
    challenge_id = str(challenge["id"])
    kind = str(oracle.get("oracle_kind") or "")
    dimensions = list(challenge.get("dimensions") or [])
    if kind == "stress_case_signature":
        stress_id = str((challenge.get("public_input") or {}).get("stress_case_id") or "")
        observed = stress_cases.get(stress_id)
        expected = str((oracle.get("private_expected") or {}).get("stress_case_status") or "")
        if observed is None:
            status = "FAIL"
            detail = {"reason": "stress_case_missing", "stress_case_id": stress_id}
        elif expected == "PASS":
            status = "PASS" if observed.get("status") == "PASS" else "FAIL"
            detail = {"stress_case_id": stress_id, "observed_status": observed.get("status")}
        else:
            canonical_known = set(known.get("canonical_blind_spot_case_ids") or [])
            status = "KNOWN_DIAGNOSTIC" if stress_id in canonical_known and observed.get("status") == "FAIL" else "FAIL"
            detail = {"stress_case_id": stress_id, "observed_status": observed.get("status"), "expected": expected}
        return {"id": challenge_id, "layer": challenge["layer"], "status": status, "dimensions": dimensions, "detail": detail}
    if response is None:
        return {"id": challenge_id, "layer": challenge["layer"], "status": "UNKNOWN", "dimensions": dimensions, "detail": {"reason": "response_missing"}}
    public = challenge.get("public_input") if isinstance(challenge.get("public_input"), dict) else {}
    expected = oracle.get("private_expected") if isinstance(oracle.get("private_expected"), dict) else {}
    passed = False
    detail: dict[str, Any]
    if kind == "dependency_plan":
        touched = response.get("touch") if isinstance(response.get("touch"), list) else []
        required = expected.get("required_touched") if isinstance(expected.get("required_touched"), list) else []
        forbidden = expected.get("forbidden_touched") if isinstance(expected.get("forbidden_touched"), list) else []
        missing = sorted(set(required) - set(touched))
        forbidden_seen = sorted(set(forbidden) & set(touched))
        passed = not missing and not forbidden_seen
        detail = {"missing_required": missing, "forbidden_touched": forbidden_seen}
    elif kind == "state_machine":
        truth = state_machine_truth(public)
        passed = response == truth
        detail = {"truth": truth}
    elif kind == "hidden_decision":
        passed = response.get("decision") == expected.get("decision") and _same_sets(response.get("violations"), expected.get("violations"))
        detail = {"expected_decision": expected.get("decision"), "expected_violations": expected.get("violations")}
    elif kind == "security_controls":
        controls = set(map(str, response.get("controls") or []))
        required = set(map(str, expected.get("required_controls") or []))
        forbidden = set(map(str, expected.get("forbidden_controls") or []))
        missing = sorted(required - controls)
        unsafe = sorted(forbidden & controls)
        passed = response.get("decision") == "accept" and not missing and not unsafe
        detail = {"missing_controls": missing, "forbidden_controls": unsafe}
    elif kind == "web_reducer":
        truth = web_reducer_truth(public)
        passed = response == truth
        detail = {"truth": truth}
    elif kind == "service_dag":
        passed, detail = service_order_valid(public, response)
    elif kind == "causal_chain":
        truth = causal_chain_truth(public)
        passed = _same_sets(response.get("root_failures"), truth.get("root_failures"))
        detail = {"truth": truth}
    elif kind == "metamorphic":
        truth = metamorphic_truth(public)
        passed = response == truth
        detail = {"truth": truth}
    elif kind == "contamination_guard":
        truth = contamination_truth(public)
        passed = response.get("eligible") == truth["eligible"] and _same_sets(response.get("reasons"), truth["reasons"])
        detail = {"truth": truth}
    elif kind == "cpm":
        truth = cpm_truth(public)
        passed = response == truth
        detail = {"truth": truth}
    elif kind == "resource_schedule":
        passed, detail = resource_schedule_valid(public, response)
    elif kind == "time_cost":
        passed, detail = time_cost_valid(public, response)
    elif kind == "agent_integrity":
        truth = agent_integrity_truth(public)
        passed = response.get("decision") == truth["decision"] and _same_sets(response.get("violations"), truth["violations"])
        detail = {"truth": truth}
    elif kind == "governance":
        truth = governance_truth(public)
        passed = response.get("decision") == truth["decision"] and _same_sets(response.get("violations"), truth["violations"])
        detail = {"truth": truth}
    else:
        raise ValueError(f"unknown oracle kind {kind} for {challenge_id}")
    return {"id": challenge_id, "layer": challenge["layer"], "status": "PASS" if passed else "FAIL", "dimensions": dimensions, "detail": detail}


def run_research_stress(repo_root: Path, known: dict[str, Any]) -> dict[str, Any]:
    script = repo_root / "tests" / "p4_eval_pack" / "run_p4_research_stress_suite.py"
    proc = subprocess.run([sys.executable, str(script), "--repo-root", str(repo_root)], cwd=repo_root, text=True, capture_output=True)
    try:
        result = json.loads(proc.stdout)
    except Exception as exc:
        return {"status": "DRIFT", "exit_code": proc.returncode, "error": f"stress runner JSON parse failed: {exc}", "output_tail": (proc.stdout + proc.stderr)[-1600:], "cases": {}}
    cases = {str(item.get("id")): item for item in result.get("cases", []) if isinstance(item, dict)}
    failed_ids = sorted(case_id for case_id, item in cases.items() if item.get("status") == "FAIL")
    blind_spots = sorted(str(item) for item in result.get("blind_spots", []))
    expected_failed_ids = sorted(str(item) for item in known.get("expected_failed_case_ids", []))
    expected_blind_spots = sorted(str(item) for item in known.get("expected_blind_spots", []))
    signature_matches = (
        result.get("runner") == known.get("stress_runner")
        and int(result.get("case_count") or 0) == int(known.get("expected_case_count") or -1)
        and int(result.get("passed") or 0) == int(known.get("expected_passed") or -1)
        and int(result.get("failed") or 0) == int(known.get("expected_failed") or -1)
        and failed_ids == expected_failed_ids
        and blind_spots == expected_blind_spots
        and proc.returncode == 1
        and result.get("canonical_before") == result.get("canonical_after")
        and (result.get("evidence_policy") or {}).get("promotion_eligible") is False
        and (result.get("evidence_policy") or {}).get("canonical_mutation_allowed") is False
    )
    return {
        "status": "KNOWN_DIAGNOSTIC_STABLE" if signature_matches else "DRIFT",
        "exit_code": proc.returncode,
        "signature_matches": signature_matches,
        "case_count": result.get("case_count"),
        "passed": result.get("passed"),
        "failed": result.get("failed"),
        "failed_case_ids": failed_ids,
        "blind_spots": blind_spots,
        "canonical_blind_spot_case_ids": list(known.get("canonical_blind_spot_case_ids") or []),
        "fixture_defect_case_ids": list(known.get("fixture_defect_case_ids") or []),
        "cases": cases,
    }


def response_map(path: Path | None, oracle_doc: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if path is None:
        return {
            str(item["id"]): item.get("reference_response")
            for item in oracle_doc.get("oracles", [])
            if isinstance(item, dict)
        }, "reference_self_test"
    raw = load_json(path)
    values = raw.get("responses") if isinstance(raw.get("responses"), dict) else raw
    if not isinstance(values, dict):
        raise ValueError("response file must be an object or contain a responses object")
    return {str(key): value for key, value in values.items() if isinstance(value, dict)}, "external_responses"


def summarize_dimensions(results: list[dict[str, Any]]) -> dict[str, Any]:
    counters: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "fail": 0, "known_diagnostic": 0, "unknown": 0})
    for result in results:
        bucket = {"PASS": "pass", "FAIL": "fail", "KNOWN_DIAGNOSTIC": "known_diagnostic", "UNKNOWN": "unknown"}[result["status"]]
        for dimension in result.get("dimensions") or []:
            counters[str(dimension)][bucket] += 1
    output: dict[str, Any] = {}
    for dimension, counts in sorted(counters.items()):
        scored = counts["pass"] + counts["fail"]
        output[dimension] = {
            **counts,
            "scored": scored,
            "score": round(counts["pass"] / scored, 6) if scored else None,
            "unknown_is_not_zero": True,
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the research-grounded multilayer coding-web benchmark suite.")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--responses", type=Path, default=None, help="Optional model response JSON. Missing answers remain UNKNOWN.")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--strict-known-diagnostics", action="store_true", help="Fail while known canonical blind spots remain.")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(HERE)
    if repo_root is None:
        raise SystemExit("repository root was not found")

    catalog = load_json(CATALOG_PATH)
    oracle_doc = load_json(ORACLE_PATH)
    sources = load_json(SOURCE_PATH)
    known = load_json(KNOWN_PATH)
    bundle = validate_bundle(catalog, oracle_doc, sources, known)
    responses, response_mode = response_map(args.responses, oracle_doc)
    before = canonical_snapshot(reporter(repo_root))
    stress = run_research_stress(repo_root, known)
    stress_cases = stress.pop("cases")
    oracle_by_id = {str(item["id"]): item for item in oracle_doc["oracles"]}
    results = [
        grade_one(item, oracle_by_id[str(item["id"])], responses.get(str(item["id"])), stress_cases=stress_cases, known=known)
        for item in catalog["challenges"]
    ]
    after = canonical_snapshot(reporter(repo_root))
    canonical_unchanged = before == after
    failures = [item for item in results if item["status"] == "FAIL"]
    unknown = [item for item in results if item["status"] == "UNKNOWN"]
    known_diagnostics = [item for item in results if item["status"] == "KNOWN_DIAGNOSTIC"]
    strict_blocked = bool(args.strict_known_diagnostics and known_diagnostics)
    regression_ok = stress.get("status") == "KNOWN_DIAGNOSTIC_STABLE" and canonical_unchanged and not failures
    if not regression_ok or strict_blocked:
        status = "FAIL"
        exit_code = 1
    elif response_mode == "external_responses" and unknown:
        status = "INCOMPLETE"
        exit_code = 2
    else:
        status = "PASS"
        exit_code = 0
    layer_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "fail": 0, "known_diagnostic": 0, "unknown": 0})
    for item in results:
        key = {"PASS": "pass", "FAIL": "fail", "KNOWN_DIAGNOSTIC": "known_diagnostic", "UNKNOWN": "unknown"}[item["status"]]
        layer_counts[str(item["layer"])][key] += 1
    output = {
        "schema_version": 1,
        "runner": "coding-web-multilayer-suite-v1",
        "status": status,
        "response_mode": response_mode,
        "strict_known_diagnostics": bool(args.strict_known_diagnostics),
        "evidence_policy": catalog["evidence_policy"],
        "bundle_validation": bundle,
        "research_stress": stress,
        "canonical_before": before,
        "canonical_after": after,
        "canonical_non_interference": "PASS" if canonical_unchanged else "FAIL",
        "challenge_summary": {
            "total": len(results),
            "passed": sum(item["status"] == "PASS" for item in results),
            "failed": len(failures),
            "known_diagnostics": len(known_diagnostics),
            "unknown": len(unknown),
        },
        "dimension_scores": summarize_dimensions(results),
        "layer_counts": dict(sorted(layer_counts.items())),
        "known_diagnostic_policy": {
            "default_regression_mode": "known signature is reported but not scored as zero",
            "strict_mode": "known canonical blind spots fail the run",
            "signature_change_requires_review": True,
            "fixture_defects_are_reported_separately": True,
        },
        "challenges": results,
    }
    rendered = json.dumps(output, indent=2, sort_keys=True)
    if args.json_out:
        target = args.json_out if args.json_out.is_absolute() else repo_root / args.json_out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
