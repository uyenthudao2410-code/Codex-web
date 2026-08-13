from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from coding_tools_mcp.server import Runtime


SCENARIO_VERSION = 1
WORKLOAD = (
    {
        "class": "deterministic",
        "count": 30,
        "workflow": "custom",
        "requested": "deterministic",
        "strong_oracle": True,
        "prepared": {"selected_paths": ["proof.txt"], "total_content_bytes": 128},
    },
    {
        "class": "localized_strong_oracle",
        "count": 35,
        "workflow": "bugfix",
        "requested": "auto",
        "strong_oracle": True,
        "prepared": {"selected_paths": ["app.py", "test_app.py"], "total_content_bytes": 20_000},
    },
    {
        "class": "bounded_leaf",
        "count": 20,
        "workflow": "feature",
        "requested": "auto",
        "strong_oracle": False,
        "prepared": {"selected_paths": ["a.py", "b.py", "c.py"], "total_content_bytes": 50_000},
    },
    {
        "class": "broad_deep",
        "count": 15,
        "workflow": "feature",
        "requested": "auto",
        "strong_oracle": False,
        "prepared": {"selected_paths": [f"f{i}.py" for i in range(8)], "total_content_bytes": 90_000},
    },
)

# Scenario constants are intentionally explicit. They are not production billing data.
CREDITS_PER_ATTEMPT = {"mini": 0.138, "luna": 0.260, "sol_xhigh": 1.317, "deterministic": 0.0}
TTA_SECONDS = {"mini": 10.2, "luna": 10.1, "sol_xhigh": 11.2, "deterministic": 3.3}
SUCCESS_PROBABILITY = {
    "localized_strong_oracle": {"mini": 0.75, "sol_xhigh": 0.97},
    "bounded_leaf": {"luna": 0.85, "sol_xhigh": 0.95},
    "broad_deep": {"sol_xhigh": 0.92},
    "deterministic": {"deterministic": 1.0},
}
SERIAL_FALLBACK_PENALTY_SECONDS = 22.8


def _route_distribution() -> tuple[dict[str, int], list[dict[str, Any]]]:
    distribution: dict[str, int] = {}
    decisions: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temp:
        runtime = Runtime(Path(temp), permission_mode="safe")
        try:
            for item in WORKLOAD:
                route = runtime._select_agent_execution_route(
                    workflow=str(item["workflow"]),
                    prepared=dict(item["prepared"]),
                    requested=str(item["requested"]),
                    allow_high_cost=False,
                    strong_oracle=bool(item["strong_oracle"]),
                )
                selected = str(route["selected"])
                count = int(item["count"])
                distribution[selected] = distribution.get(selected, 0) + count
                decisions.append(
                    {
                        "class": item["class"],
                        "count": count,
                        "selected": selected,
                        "reason": route.get("reason"),
                        "model": route.get("model"),
                        "effort": route.get("effort"),
                    }
                )
        finally:
            runtime.close()
    return distribution, decisions


def _adaptive_economics(decisions: list[dict[str, Any]]) -> dict[str, float]:
    credits = 0.0
    accepted = 0.0
    seconds = 0.0
    wasted_attempts = 0.0
    for decision in decisions:
        task_class = str(decision["class"])
        count = int(decision["count"])
        route = str(decision["selected"])
        if route == "deterministic":
            credits += count * CREDITS_PER_ATTEMPT[route]
            seconds += count * TTA_SECONDS[route]
            accepted += count
            continue
        primary_p = SUCCESS_PROBABILITY[task_class][route]
        credits += count * CREDITS_PER_ATTEMPT[route]
        seconds += count * TTA_SECONDS[route]
        if route in {"mini", "luna"}:
            fallback_p = SUCCESS_PROBABILITY[task_class]["sol_xhigh"]
            fail_count = count * (1.0 - primary_p)
            wasted_attempts += fail_count
            credits += fail_count * CREDITS_PER_ATTEMPT["sol_xhigh"]
            seconds += fail_count * (TTA_SECONDS["sol_xhigh"] + SERIAL_FALLBACK_PENALTY_SECONDS)
            accepted += count * (primary_p + (1.0 - primary_p) * fallback_p)
        else:
            accepted += count * primary_p
    return {
        "credits": round(credits, 4),
        "accepted": round(accepted, 4),
        "credits_per_accepted": round(credits / accepted, 4),
        "tta_hours": round(seconds / 3600.0, 4),
        "wasted_attempts": round(wasted_attempts, 4),
    }


def _all_sol_economics() -> dict[str, float]:
    credits = 0.0
    accepted = 0.0
    seconds = 0.0
    for item in WORKLOAD:
        task_class = str(item["class"])
        count = int(item["count"])
        if task_class == "deterministic":
            accepted += count
            seconds += count * TTA_SECONDS["deterministic"]
            continue
        credits += count * CREDITS_PER_ATTEMPT["sol_xhigh"]
        seconds += count * TTA_SECONDS["sol_xhigh"]
        accepted += count * SUCCESS_PROBABILITY[task_class]["sol_xhigh"]
    return {
        "credits": round(credits, 4),
        "accepted": round(accepted, 4),
        "credits_per_accepted": round(credits / accepted, 4),
        "tta_hours": round(seconds / 3600.0, 4),
        "wasted_attempts": 0.0,
    }


def simulate() -> dict[str, Any]:
    distribution, decisions = _route_distribution()
    adaptive = _adaptive_economics(decisions)
    all_sol = _all_sol_economics()
    return {
        "benchmark": "routing economics scenario",
        "scenario_version": SCENARIO_VERSION,
        "evidence_class": "scenario_simulation_not_production_ab",
        "task_count": sum(int(item["count"]) for item in WORKLOAD),
        "production_router_invoked": True,
        "route_distribution": distribution,
        "decisions": decisions,
        "assumptions": {
            "credits_per_attempt": CREDITS_PER_ATTEMPT,
            "tta_seconds": TTA_SECONDS,
            "success_probability": SUCCESS_PROBABILITY,
            "serial_fallback_penalty_seconds": SERIAL_FALLBACK_PENALTY_SECONDS,
            "policy": "deterministic lane stays model-free; Mini/Luna receive at most one Sol xhigh fallback; Sol xhigh has no model fallback",
        },
        "strategies": {"adaptive_router": adaptive, "all_sol_for_model_tasks": all_sol},
        "adaptive_credit_saving_vs_all_sol_percent": round((1.0 - adaptive["credits"] / all_sol["credits"]) * 100.0, 2),
        "note": "Costs/probabilities are explicit scenario assumptions anchored to prior local research. Use route ledger observations for production calibration; do not read this as an A/B measurement.",
    }


def main() -> None:
    payload = simulate()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    report_dir = Path(__file__).resolve().parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = report_dir / f"routing-economics-{stamp}.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"report: {target}")


if __name__ == "__main__":
    main()
