from __future__ import annotations

"""Task-control handling for pre-mutation P4 solution-shadow evidence."""

from typing import Any

from .errors import ToolFailure
from .solution_economics import record_solution_shadow, solution_shadow_run_report


class SolutionShadowControlMixin:
    def _solution_shadow_control(
        self,
        args: dict[str, Any],
        recommendation: Any,
        *,
        transport: str,
    ) -> dict[str, Any]:
        _state, projection, run_id, wave_id = self._coordination_ids(args)
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "No orchestration run is available for solution shadow evidence.", category="not_found")
        recording = None
        context_recovered = False
        if recommendation is not None:
            if not isinstance(recommendation, dict):
                raise ToolFailure("SOLUTION_SHADOW_INVALID", "solution shadow recommendation must be an object.", category="validation")
            projected_run = str(projection.get("run_id") or "").strip()
            projected_wave = str(projection.get("wave_id") or "").strip()
            if run_id != projected_run or not wave_id or wave_id != projected_wave:
                explicit_run = str(args.get("run_id") or "").strip()
                explicit_wave = str(args.get("wave_id") or "").strip()
                ctx = self.orchestration_control.snapshot(run_id) if explicit_run and explicit_wave else None
                if (
                    ctx is None
                    or ctx.run_id != explicit_run
                    or ctx.wave_id != explicit_wave
                    or ctx.state not in {"PREFLIGHT", "READY"}
                ):
                    raise ToolFailure(
                        "SOLUTION_SHADOW_CONTEXT_MISMATCH",
                        "Solution shadow recording requires the current task-projected run/wave or an explicit current PREFLIGHT/READY run/wave.",
                        category="runtime",
                        retryable=True,
                        details={
                            "run_id": run_id,
                            "wave_id": wave_id,
                            "projected_run_id": projected_run,
                            "projected_wave_id": projected_wave,
                            "explicit_context_recovery": bool(explicit_run and explicit_wave),
                        },
                    )
                self._require_hub_controller(run_id)
                context_recovered = True
            else:
                ctx = self.orchestration_control.snapshot(run_id)
                self._require_hub_controller(run_id)
            try:
                recording = record_solution_shadow(
                    self.orchestration_ledger,
                    run_id=run_id,
                    wave_id=wave_id,
                    recommendation=recommendation,
                )
            except ValueError as exc:
                raise ToolFailure("SOLUTION_SHADOW_INVALID", str(exc), category="validation", retryable=False) from exc
            if context_recovered and ctx is not None:
                self._project_orchestration(ctx, event="solution_shadow_context_recovered")
        return {
            "recording": recording,
            "solution_shadow": solution_shadow_run_report(self.orchestration_ledger, run_id),
            "transport": transport,
            "context_recovered": context_recovered,
            "production_behavior_changed": False,
        }
