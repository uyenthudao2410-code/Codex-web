from __future__ import annotations

from pathlib import Path
from typing import Any

from .orchestration_ledger import OrchestrationLedger


class OrchestrationReport:
    """Generate human-readable reports exclusively from the canonical ledger."""

    def __init__(self, workspace: Path, ledger: OrchestrationLedger) -> None:
        self.workspace = workspace.resolve(strict=False)
        self.ledger = ledger
        self.report_root = self.workspace / ".coding-tools" / "orchestration" / "reports"

    @staticmethod
    def _cell(value: Any) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")

    def render_wave(self, run_id: str, wave_id: str) -> str:
        run = self.ledger.get_run(run_id) or {}
        wave = next((item for item in self.ledger.list_waves(run_id) if item["wave_id"] == wave_id), None)
        if wave is None:
            raise KeyError(f"Unknown wave: {wave_id}")
        events = self.ledger.list_events(run_id, wave_id=wave_id)
        proofs = self.ledger.list_proofs(run_id, wave_id=wave_id)
        delegations = self.ledger.list_delegations(wave_id)
        lines = [
            f"# Orchestration Wave {wave['ordinal']}",
            "",
            f"- Run: `{run_id}`",
            f"- Wave: `{wave_id}`",
            f"- Objective: {run.get('objective', '')}",
            f"- Mode: `{wave['execution_mode']}`",
            f"- Base HEAD: `{wave['base_head']}`",
            f"- Worktree fingerprint: `{wave['worktree_fp']}`",
            f"- Contract fingerprint: `{wave['contract_fp']}`",
            f"- Status: **{wave['status']}**",
            "",
            "## Delegations",
            "",
            "| ID | Owner | Requested | Resolved | Model | Effort | Status |",
            "|---|---|---|---|---|---|---|",
        ]
        if delegations:
            for item in delegations:
                lines.append(
                    "| " + " | ".join(
                        self._cell(value)
                        for value in (
                            item["delegation_id"], item["authority_owner"], item["route_requested"],
                            item["route_resolved"], item["model"], item["effort"], item["status"],
                        )
                    ) + " |"
                )
        else:
            lines.append("| - | - | - | - | - | - | - |")
        lines.extend([
            "",
            "## State / event timeline",
            "",
            "| Seq | Time | Event | From | To | Key evidence |",
            "|---:|---|---|---|---|---|",
        ])
        for event in events:
            payload = event.get("payload") or {}
            interesting = []
            for key in (
                "reason", "failure_class", "requested", "resolved", "authority_owner", "owner", "stage_id",
                "status", "cache_hit", "lease_id", "input_fingerprint",
            ):
                if key in payload and payload[key] not in (None, "", []):
                    interesting.append(f"{key}={payload[key]}")
            lines.append(
                "| " + " | ".join(
                    self._cell(value)
                    for value in (
                        event["seq"], event["event_time"], event["event_type"], event["state_before"],
                        event["state_after"], "; ".join(interesting),
                    )
                ) + " |"
            )
        lines.extend([
            "",
            "## Proof",
            "",
            "| Stage | Status | Fingerprint | Cache | Duration ms | Exit |",
            "|---|---|---|---:|---:|---:|",
        ])
        if proofs:
            for proof in proofs:
                lines.append(
                    "| " + " | ".join(
                        self._cell(value)
                        for value in (
                            proof["stage_id"], proof["status"], proof["input_fingerprint"], proof["cache_hit"],
                            proof["duration_ms"], proof["exit_code"],
                        )
                    ) + " |"
                )
        else:
            lines.append("| - | - | - | - | - | - |")
        integrity = self.ledger.verify_chain(run_id)
        lines.extend([
            "",
            "## Audit integrity",
            "",
            f"- Hash chain valid: **{integrity.get('ok')}**",
            f"- Events checked: `{integrity.get('checked', 0)}`",
            f"- Chain head: `{integrity.get('head_hash', '')}`",
            "",
        ])
        return "\n".join(lines)

    def render_run(self, run_id: str) -> str:
        run = self.ledger.get_run(run_id)
        if run is None:
            raise KeyError(f"Unknown run: {run_id}")
        waves = self.ledger.list_waves(run_id)
        events = self.ledger.list_events(run_id)
        proofs = self.ledger.list_proofs(run_id)
        route_events = [item for item in events if item["event_type"] == "route_selected"]
        failure_events = [item for item in events if item["event_type"] == "failure_observed"]
        replan_count = sum(1 for item in events if item.get("state_after") == "REPLAN")
        cache_hits = sum(1 for item in proofs if item.get("cache_hit"))
        lines = [
            "# Orchestration Run Summary",
            "",
            f"- Run: `{run_id}`",
            f"- Task: `{run.get('task_id', '')}`",
            f"- Objective: {run.get('objective', '')}",
            f"- Status: **{run.get('status', '')}**",
            f"- Started: `{run.get('started_at', '')}`",
            f"- Finished: `{run.get('finished_at', '')}`",
            "",
            "## Outcome metrics",
            "",
            f"- Waves: **{len(waves)}**",
            f"- Route decisions: **{len(route_events)}**",
            f"- Failures observed: **{len(failure_events)}**",
            f"- REPLAN transitions: **{replan_count}**",
            f"- Proof stages: **{len(proofs)}**",
            f"- Proof cache hits: **{cache_hits}**",
            "",
            "## Waves",
            "",
            "| # | Wave | Mode | Base | Status |",
            "|---:|---|---|---|---|",
        ]
        for wave in waves:
            lines.append(
                f"| {wave['ordinal']} | `{wave['wave_id']}` | `{wave['execution_mode']}` | `{wave['base_head']}` | {wave['status']} |"
            )
        lines.extend([
            "",
            "## Route decisions",
            "",
            "| Seq | Requested | Resolved | Reason |",
            "|---:|---|---|---|",
        ])
        for event in route_events:
            payload = event.get("payload") or {}
            lines.append(
                f"| {event['seq']} | `{self._cell(payload.get('requested'))}` | `{self._cell(payload.get('resolved'))}` | {self._cell(payload.get('reason'))} |"
            )
        lines.extend([
            "",
            "## Failures / replans",
            "",
            "| Seq | Failure class | State | Evidence |",
            "|---:|---|---|---|",
        ])
        for event in failure_events:
            payload = event.get("payload") or {}
            lines.append(
                f"| {event['seq']} | `{self._cell(payload.get('failure_class'))}` | `{event.get('state_before','')}` | {self._cell(payload.get('reason') or '')} |"
            )
        integrity = self.ledger.verify_chain(run_id)
        lines.extend([
            "",
            "## Audit integrity",
            "",
            f"- Hash chain valid: **{integrity.get('ok')}**",
            f"- Events checked: `{integrity.get('checked', 0)}`",
            f"- Chain head: `{integrity.get('head_hash', '')}`",
            "",
            "> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.",
            "",
        ])
        return "\n".join(lines)

    def write_reports(self, run_id: str) -> dict[str, Any]:
        run_dir = self.report_root / f"run-{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        run_path = run_dir / "run-summary.md"
        run_path.write_text(self.render_run(run_id), encoding="utf-8")
        wave_paths: list[str] = []
        for wave in self.ledger.list_waves(run_id):
            path = run_dir / f"wave-{int(wave['ordinal']):03d}.md"
            path.write_text(self.render_wave(run_id, wave["wave_id"]), encoding="utf-8")
            wave_paths.append(str(path))
        return {"run_report": str(run_path), "wave_reports": wave_paths}
