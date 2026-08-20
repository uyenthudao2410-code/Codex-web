from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PASS_STATUSES = frozenset({"FIRST_PASS", "REPAIRED"})
KNOWN_STATUSES = frozenset({"FIRST_PASS", "REPAIRED", "FAIL", "HARD_FAIL", "UNKNOWN"})
ARTIFACT_RELATIVE_PATHS = {
    "public_catalog": Path("tests/model_eval_pack/public/model_extreme_challenges_v1.json"),
    "public_feedback": Path("tests/model_eval_pack/public/model_extreme_feedback_v1.json"),
    "private_oracle": Path("tests/model_eval_pack/private/model_extreme_oracles_v1.json"),
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def recompute_observation(report: dict[str, Any]) -> dict[str, Any]:
    challenges = report.get("challenges") if isinstance(report.get("challenges"), list) else []
    statuses = [str(item.get("status") or "UNKNOWN").upper() for item in challenges if isinstance(item, dict)]
    unknown_statuses = sorted({status for status in statuses if status not in KNOWN_STATUSES})
    if unknown_statuses:
        raise ValueError(f"unknown challenge statuses: {unknown_statuses}")

    first_pass = sum(status == "FIRST_PASS" for status in statuses)
    repaired = sum(status == "REPAIRED" for status in statuses)
    failed = sum(status == "FAIL" for status in statuses)
    hard_fail = sum(status == "HARD_FAIL" for status in statuses)
    unknown = sum(status == "UNKNOWN" for status in statuses)
    total = len(statuses)
    attempted = total - unknown
    repair_opportunities = sum(
        bool(item.get("repair_opportunity"))
        for item in challenges
        if isinstance(item, dict)
    )
    summary = {
        "total": total,
        "attempted": attempted,
        "first_pass": first_pass,
        "repaired": repaired,
        "failed": failed,
        "hard_fail_count": hard_fail,
        "unknown": unknown,
        "first_pass_rate": _rate(first_pass, attempted),
        "repair_recovery_rate": _rate(repaired, repair_opportunities),
        "final_pass_rate": _rate(first_pass + repaired, attempted),
        "unknown_coverage": _rate(unknown, total),
        "unknown_is_not_zero": True,
    }

    declared = report.get("dimension_scores") if isinstance(report.get("dimension_scores"), dict) else {}
    dimension_names = sorted(
        {
            str(dimension)
            for item in challenges
            if isinstance(item, dict)
            for dimension in (item.get("dimensions") if isinstance(item.get("dimensions"), list) else [])
            if str(dimension)
        }
    )
    dimensions: dict[str, dict[str, Any]] = {}
    weighted_numerator = 0.0
    weighted_denominator = 0.0
    for name in dimension_names:
        scoped = [
            item
            for item in challenges
            if isinstance(item, dict)
            and name in (item.get("dimensions") if isinstance(item.get("dimensions"), list) else [])
        ]
        pass_count = sum(str(item.get("status") or "").upper() in PASS_STATUSES for item in scoped)
        unknown_count = sum(str(item.get("status") or "").upper() == "UNKNOWN" for item in scoped)
        observed = len(scoped) - unknown_count
        fail_count = observed - pass_count
        raw_score = pass_count / observed if observed else None
        score = round(raw_score, 6) if raw_score is not None else None
        weight_value = (declared.get(name) or {}).get("weight") if isinstance(declared.get(name), dict) else None
        if not isinstance(weight_value, (int, float)) or isinstance(weight_value, bool) or weight_value <= 0:
            raise ValueError(f"missing positive dimension weight for {name}")
        weight = float(weight_value)
        dimensions[name] = {
            "pass": pass_count,
            "fail": fail_count,
            "unknown": unknown_count,
            "observed": observed,
            "score": score,
            "weight": weight,
            "unknown_is_not_zero": True,
        }
        if raw_score is not None:
            weighted_numerator += raw_score * weight
            weighted_denominator += weight
    weighted = round(weighted_numerator / weighted_denominator, 6) if weighted_denominator else None
    return {"summary": summary, "dimension_scores": dimensions, "observed_weighted_score": weighted}


def verify_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        recomputed = recompute_observation(report)
    except ValueError as exc:
        return [str(exc)]

    declared_summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    for key, expected in recomputed["summary"].items():
        if declared_summary.get(key) != expected:
            errors.append(f"summary.{key}: declared={declared_summary.get(key)!r} recomputed={expected!r}")

    declared_dimensions = report.get("dimension_scores") if isinstance(report.get("dimension_scores"), dict) else {}
    if set(declared_dimensions) != set(recomputed["dimension_scores"]):
        errors.append("dimension_scores keys do not match challenge dimensions")
    for name, expected in recomputed["dimension_scores"].items():
        actual = declared_dimensions.get(name) if isinstance(declared_dimensions.get(name), dict) else {}
        for key in ("pass", "fail", "unknown", "observed", "score", "weight", "unknown_is_not_zero"):
            if actual.get(key) != expected.get(key):
                errors.append(f"dimension_scores.{name}.{key}: declared={actual.get(key)!r} recomputed={expected.get(key)!r}")

    if report.get("observed_weighted_score") != recomputed["observed_weighted_score"]:
        errors.append(
            "observed_weighted_score: "
            f"declared={report.get('observed_weighted_score')!r} recomputed={recomputed['observed_weighted_score']!r}"
        )
    if report.get("canonical_before") != report.get("canonical_after"):
        errors.append("canonical_before and canonical_after differ")
    if report.get("canonical_non_interference") != "PASS":
        errors.append("canonical_non_interference must be PASS")
    policy = report.get("evidence_policy") if isinstance(report.get("evidence_policy"), dict) else {}
    if policy.get("source_class") != "benchmark":
        errors.append("evidence_policy.source_class must be benchmark")
    for key in ("promotion_eligible", "canonical_mutation_allowed", "p5_automatic_start", "automatic_policy_activation"):
        if policy.get(key) is not False:
            errors.append(f"evidence_policy.{key} must remain false")
    if str(report.get("response_mode") or "") != "external_model_responses":
        errors.append("response_mode must be external_model_responses for external closeout")
    return errors


def _artifact_entry(repo_root: Path, path: Path) -> dict[str, str]:
    resolved = path.resolve()
    try:
        display = resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        display = str(resolved)
    return {"path": display, "sha256": _sha256(resolved)}


def build_manifest(
    *,
    repo_root: Path,
    report_path: Path,
    responses_path: Path,
    candidate_model: str,
    evaluation_date: str,
    expected_private_oracle_sha256: str,
    extreme_requested_effort: str = "medium",
    extreme_resolved_effort: str = "medium",
    ultra_requested_effort: str = "medium",
    ultra_resolved_effort: str = "low",
    ultra_fallback_reason: str = "medium_no_terminal_answer_within_budget",
    expected_extreme_count: int = 24,
    expected_ultra_count: int = 6,
) -> dict[str, Any]:
    root = repo_root.resolve()
    report = _load_json(report_path)
    report_errors = verify_report(report)
    if report_errors:
        raise ValueError("report verification failed: " + "; ".join(report_errors))
    if not candidate_model.strip():
        raise ValueError("candidate_model is required")
    if not evaluation_date.strip():
        raise ValueError("evaluation_date is required")

    artifacts: dict[str, dict[str, str]] = {}
    for name, relative in ARTIFACT_RELATIVE_PATHS.items():
        target = root / relative
        if not target.is_file():
            raise ValueError(f"missing {name}: {target}")
        artifacts[name] = _artifact_entry(root, target)
    artifacts["responses"] = _artifact_entry(root, responses_path)
    artifacts["final_report"] = _artifact_entry(root, report_path)

    oracle_sha = artifacts["private_oracle"]["sha256"]
    expected_oracle_sha = expected_private_oracle_sha256.strip().lower()
    if oracle_sha != expected_oracle_sha:
        raise ValueError(f"private oracle hash mismatch: observed={oracle_sha} expected={expected_oracle_sha}")

    challenges = report.get("challenges") if isinstance(report.get("challenges"), list) else []
    tier_counts = {
        "Extreme": sum(str(item.get("tier") or "") == "Extreme" for item in challenges if isinstance(item, dict)),
        "Ultra": sum(str(item.get("tier") or "") == "Ultra" for item in challenges if isinstance(item, dict)),
    }
    if tier_counts != {"Extreme": expected_extreme_count, "Ultra": expected_ultra_count}:
        raise ValueError(f"unexpected tier counts: {tier_counts}")

    case_effort: dict[str, dict[str, Any]] = {}
    for item in challenges:
        if not isinstance(item, dict):
            continue
        challenge_id = str(item.get("id") or "")
        tier = str(item.get("tier") or "")
        if tier == "Extreme":
            requested, resolved, reason = extreme_requested_effort, extreme_resolved_effort, None
        elif tier == "Ultra":
            requested, resolved, reason = ultra_requested_effort, ultra_resolved_effort, ultra_fallback_reason
        else:
            raise ValueError(f"unsupported tier in final report: {tier!r}")
        case_effort[challenge_id] = {
            "tier": tier,
            "requested_effort": requested,
            "resolved_effort": resolved,
            "fallback": requested != resolved,
            "fallback_reason": reason if requested != resolved else None,
        }

    observation = recompute_observation(report)
    return {
        "schema_version": 1,
        "kind": "p4_mx_external_evaluation_closeout",
        "provenance": "evaluator_owned_not_trusted_for_correctness_scoring",
        "evaluation_date": evaluation_date.strip(),
        "candidate_model": candidate_model.strip(),
        "runner": str(report.get("runner") or ""),
        "response_mode": str(report.get("response_mode") or ""),
        "effort_policy": {
            "Extreme": {
                "count": tier_counts["Extreme"],
                "requested_effort": extreme_requested_effort,
                "resolved_effort": extreme_resolved_effort,
                "fallback": extreme_requested_effort != extreme_resolved_effort,
            },
            "Ultra": {
                "count": tier_counts["Ultra"],
                "requested_effort": ultra_requested_effort,
                "resolved_effort": ultra_resolved_effort,
                "fallback": ultra_requested_effort != ultra_resolved_effort,
                "fallback_reason": ultra_fallback_reason,
            },
            "cases": case_effort,
        },
        "transport_policy": {
            "non_terminal_medium_timeout": "transport_failure_not_model_fail",
            "fallback_preserves_candidate_model": True,
            "fallback_uses_same_public_challenge_and_private_oracle_identity": True,
        },
        "artifact_integrity": artifacts,
        "expected_observation": {
            **observation,
            "family_outcomes": report.get("family_outcomes") if isinstance(report.get("family_outcomes"), dict) else {},
        },
        "evidence_policy": dict(report.get("evidence_policy") or {}),
        "closeout_policy": {
            "benchmark_nonpromoting": True,
            "canonical_mutation_allowed": False,
            "p5_may_be_opened": False,
            "automatic_policy_activation": False,
            "model_failure_is_a_valid_closed_measurement": True,
        },
    }


def verify_manifest(
    *,
    repo_root: Path,
    report_path: Path,
    responses_path: Path,
    manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    report = _load_json(report_path)
    errors.extend(verify_report(report))
    root = repo_root.resolve()
    current_entries: dict[str, dict[str, str]] = {}
    for name, relative in ARTIFACT_RELATIVE_PATHS.items():
        target = root / relative
        if not target.is_file():
            errors.append(f"missing artifact: {name}")
            continue
        current_entries[name] = _artifact_entry(root, target)
    for name, target in (("responses", responses_path), ("final_report", report_path)):
        if not target.is_file():
            errors.append(f"missing artifact: {name}")
            continue
        current_entries[name] = _artifact_entry(root, target)

    declared_entries = manifest.get("artifact_integrity") if isinstance(manifest.get("artifact_integrity"), dict) else {}
    for name, current in current_entries.items():
        declared = declared_entries.get(name) if isinstance(declared_entries.get(name), dict) else {}
        if declared.get("sha256") != current.get("sha256"):
            errors.append(f"artifact hash mismatch: {name}")

    observation = recompute_observation(report)
    expected = manifest.get("expected_observation") if isinstance(manifest.get("expected_observation"), dict) else {}
    for key in ("summary", "dimension_scores", "observed_weighted_score"):
        if expected.get(key) != observation.get(key):
            errors.append(f"manifest expected_observation.{key} does not match report")
    if manifest.get("runner") != report.get("runner"):
        errors.append("manifest runner does not match report")
    if manifest.get("response_mode") != report.get("response_mode"):
        errors.append("manifest response_mode does not match report")

    effort = manifest.get("effort_policy") if isinstance(manifest.get("effort_policy"), dict) else {}
    cases = effort.get("cases") if isinstance(effort.get("cases"), dict) else {}
    report_ids = {
        str(item.get("id") or "")
        for item in (report.get("challenges") if isinstance(report.get("challenges"), list) else [])
        if isinstance(item, dict)
    }
    if set(cases) != report_ids:
        errors.append("effort_policy.cases must cover exactly the final report challenge IDs")

    policy = manifest.get("closeout_policy") if isinstance(manifest.get("closeout_policy"), dict) else {}
    for key in ("benchmark_nonpromoting", "model_failure_is_a_valid_closed_measurement"):
        if policy.get(key) is not True:
            errors.append(f"closeout_policy.{key} must be true")
    for key in ("canonical_mutation_allowed", "p5_may_be_opened", "automatic_policy_activation"):
        if policy.get(key) is not False:
            errors.append(f"closeout_policy.{key} must be false")
    return errors


def render_summary(report: dict[str, Any], manifest: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    dimensions = report.get("dimension_scores") if isinstance(report.get("dimension_scores"), dict) else {}
    effort = manifest.get("effort_policy") if isinstance(manifest.get("effort_policy"), dict) else {}
    extreme = effort.get("Extreme") if isinstance(effort.get("Extreme"), dict) else {}
    ultra = effort.get("Ultra") if isinstance(effort.get("Ultra"), dict) else {}
    hard_fail_ids = [
        str(item.get("id"))
        for item in (report.get("challenges") if isinstance(report.get("challenges"), list) else [])
        if isinstance(item, dict) and str(item.get("status") or "") == "HARD_FAIL"
    ]
    lines = [
        "# P4-MX External Evaluation Closeout",
        "",
        f"- Candidate model: `{manifest.get('candidate_model')}`",
        f"- Evaluation date: `{manifest.get('evaluation_date')}`",
        f"- Runner: `{manifest.get('runner')}`",
        "- Evidence class: benchmark, non-promoting, non-mutating.",
        "- Effort interpretation: "
        f"{extreme.get('count')} Extreme at `{extreme.get('resolved_effort')}` + "
        f"{ultra.get('count')} Ultra at `{ultra.get('resolved_effort')}` "
        f"(requested `{ultra.get('requested_effort')}`, fallback: `{ultra.get('fallback_reason')}`).",
        "- A response filename containing `medium` is not evidence that all cases ran at medium effort; the evaluator-owned manifest is authoritative for effort provenance.",
        "",
        "## Held-out outcome",
        "",
        f"- Total / attempted: {summary.get('total')} / {summary.get('attempted')}",
        f"- FIRST_PASS: {summary.get('first_pass')}",
        f"- REPAIRED: {summary.get('repaired')}",
        f"- FAIL: {summary.get('failed')}",
        f"- HARD_FAIL: {summary.get('hard_fail_count')}",
        f"- UNKNOWN: {summary.get('unknown')}",
        f"- First-pass rate: {summary.get('first_pass_rate')}",
        f"- Repair recovery rate: {summary.get('repair_recovery_rate')}",
        f"- Final pass rate: {summary.get('final_pass_rate')}",
        f"- Weighted score: {report.get('observed_weighted_score')}",
        f"- Hard-fail IDs: {', '.join(hard_fail_ids) if hard_fail_ids else 'none'}",
        "",
        "## Canonical dimension scores",
        "",
        "| Dimension | Pass | Fail | Observed | Score | Weight |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in sorted(dimensions):
        item = dimensions[name] if isinstance(dimensions.get(name), dict) else {}
        lines.append(
            f"| {name} | {item.get('pass')} | {item.get('fail')} | {item.get('observed')} | {item.get('score')} | {item.get('weight')} |"
        )
    lines.extend([
        "",
        "## Integrity and governance",
        "",
        f"- Canonical before/after identical: `{report.get('canonical_before') == report.get('canonical_after')}`",
        "- Non-terminal medium timeout policy: `transport_failure_not_model_fail`.",
        "- Ultra fallback preserves candidate model and public/private challenge-oracle identity.",
        "- P4-MX cannot open P5 and cannot activate routing policy.",
        "",
        "### Artifact hashes",
        "",
    ])
    artifacts = manifest.get("artifact_integrity") if isinstance(manifest.get("artifact_integrity"), dict) else {}
    for name in sorted(artifacts):
        item = artifacts[name] if isinstance(artifacts.get(name), dict) else {}
        lines.append(f"- `{name}`: `{item.get('sha256')}` | `{item.get('path')}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or replay-verify immutable evaluator-owned P4-MX closeout provenance.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--report", required=True)
    parser.add_argument("--responses", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest-out")
    group.add_argument("--manifest")
    parser.add_argument("--summary-out")
    parser.add_argument("--candidate-model")
    parser.add_argument("--evaluation-date")
    parser.add_argument("--expected-private-oracle-sha256")
    parser.add_argument("--extreme-requested-effort", default="medium")
    parser.add_argument("--extreme-resolved-effort", default="medium")
    parser.add_argument("--ultra-requested-effort", default="medium")
    parser.add_argument("--ultra-resolved-effort", default="low")
    parser.add_argument("--ultra-fallback-reason", default="medium_no_terminal_answer_within_budget")
    parser.add_argument("--expected-extreme-count", type=int, default=24)
    parser.add_argument("--expected-ultra-count", type=int, default=6)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    report_path = Path(args.report).resolve()
    responses_path = Path(args.responses).resolve()
    if args.manifest_out:
        if not args.candidate_model or not args.evaluation_date or not args.expected_private_oracle_sha256:
            parser.error("--candidate-model, --evaluation-date and --expected-private-oracle-sha256 are required when creating a manifest")
        manifest_path = Path(args.manifest_out).resolve()
        if manifest_path.exists():
            raise SystemExit(f"immutable manifest already exists: {manifest_path}")
        manifest = build_manifest(
            repo_root=root,
            report_path=report_path,
            responses_path=responses_path,
            candidate_model=args.candidate_model,
            evaluation_date=args.evaluation_date,
            expected_private_oracle_sha256=args.expected_private_oracle_sha256,
            extreme_requested_effort=args.extreme_requested_effort,
            extreme_resolved_effort=args.extreme_resolved_effort,
            ultra_requested_effort=args.ultra_requested_effort,
            ultra_resolved_effort=args.ultra_resolved_effort,
            ultra_fallback_reason=args.ultra_fallback_reason,
            expected_extreme_count=args.expected_extreme_count,
            expected_ultra_count=args.expected_ultra_count,
        )
        errors = verify_manifest(repo_root=root, report_path=report_path, responses_path=responses_path, manifest=manifest)
        if errors:
            print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
            return 1
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        manifest_path = Path(args.manifest).resolve()
        manifest = _load_json(manifest_path)
        errors = verify_manifest(repo_root=root, report_path=report_path, responses_path=responses_path, manifest=manifest)
        if errors:
            print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
            return 1

    report = _load_json(report_path)
    rendered = render_summary(report, manifest)
    if args.summary_out:
        summary_path = Path(args.summary_out).resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "status": "VERIFIED",
        "manifest": str(manifest_path),
        "candidate_model": manifest.get("candidate_model"),
        "observed_weighted_score": report.get("observed_weighted_score"),
        "model_result_status": report.get("status"),
        "automatic_policy_activation": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
