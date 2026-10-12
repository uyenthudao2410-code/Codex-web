"""Content-free read-only snapshot; never instantiates the runtime writer."""
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "resources/coding-tools-mcp/scripts"))
from report_lifecycle_census import report, _summary_payload

observed = time.time()
payload = _summary_payload(report(ROOT, observed_at=observed, grace_seconds=900, stale_after_seconds=86400))
database = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
source = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
source.execute("PRAGMA query_only=ON")
snapshot = sqlite3.connect(":memory:")
source.backup(snapshot)
source.close()
snapshot.row_factory = sqlite3.Row
snapshot.execute("PRAGMA query_only=ON")
records = {}
expected = {
    "runs": ("run_id", "95e909f0040a448faa9f1f3257e2ee2c", "a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590"),
    "waves": ("wave_id", "c101beadfc6d4f2fbc13845052c84693", "59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce"),
}
for table, (key, identity, digest) in expected.items():
    rows = snapshot.execute(f"SELECT * FROM {table} WHERE {key}=?", (identity,)).fetchall()
    if len(rows) != 1:
        raise RuntimeError("pending record not uniquely observed")
    actual = hashlib.sha256(json.dumps(dict(rows[0]), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    records[table] = {"id": identity, "sha256": actual, "unchanged": actual == digest}
snapshot.close()
payload["pending_records"] = records
payload["pending_records_unchanged"] = all(item["unchanged"] for item in records.values())
destination = Path(__file__).parent / f"final-local-observation-{int(observed * 1000)}.json"
with destination.open("x", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps({"receipt": destination.name, "integrity": payload["snapshot"]["integrity_check"],
    "summary": payload["summary"], "pending_records_unchanged": payload["pending_records_unchanged"],
    "mutated_canonical_ledger": payload["mutated_canonical_ledger"]}, sort_keys=True))
if not payload["pending_records_unchanged"]:
    raise SystemExit(2)
