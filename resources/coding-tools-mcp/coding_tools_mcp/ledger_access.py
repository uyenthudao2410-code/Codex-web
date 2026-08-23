from __future__ import annotations

from pathlib import Path

from .orchestration_ledger import OrchestrationLedger
from .ledger_analysis import LedgerAnalysisSnapshot, LedgerReadSession, open_ledger_analysis_snapshot


LEDGER_RELATIVE_PATH = Path(".coding-tools") / "orchestration" / "ledger.sqlite3"


def open_existing_ledger(workspace: Path) -> OrchestrationLedger:
    """Open an existing workspace ledger without creating missing project state."""
    root = Path(workspace).resolve(strict=False)
    ledger_path = root / LEDGER_RELATIVE_PATH
    if not ledger_path.is_file():
        raise FileNotFoundError(f"orchestration ledger does not exist: {ledger_path}")
    return OrchestrationLedger(root)


def open_existing_ledger_readonly(workspace: Path) -> LedgerReadSession:
    """Open one reader without schema initialization, WAL PRAGMAs, or commits."""
    root = Path(workspace).resolve(strict=False)
    ledger_path = root / LEDGER_RELATIVE_PATH
    if not ledger_path.is_file():
        raise FileNotFoundError(f"orchestration ledger does not exist: {ledger_path}")
    return LedgerReadSession(ledger_path)


def open_existing_ledger_analysis(workspace: Path) -> LedgerAnalysisSnapshot:
    """Create a temporary Backup-API snapshot for long-running analytics."""
    return open_ledger_analysis_snapshot(workspace)
