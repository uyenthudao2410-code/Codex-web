from __future__ import annotations

from pathlib import Path

from .orchestration_ledger import OrchestrationLedger


LEDGER_RELATIVE_PATH = Path(".coding-tools") / "orchestration" / "ledger.sqlite3"


def open_existing_ledger(workspace: Path) -> OrchestrationLedger:
    """Open an existing workspace ledger without creating missing project state."""
    root = Path(workspace).resolve(strict=False)
    ledger_path = root / LEDGER_RELATIVE_PATH
    if not ledger_path.is_file():
        raise FileNotFoundError(f"orchestration ledger does not exist: {ledger_path}")
    return OrchestrationLedger(root)
