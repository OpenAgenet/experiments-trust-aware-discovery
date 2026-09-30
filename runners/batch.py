"""Offline aggregation entry point; it never queries the core database."""
import argparse, csv, json
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--input", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args(); source = Path(args.input) / "events.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()] if source.exists() else []
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    fields = ["strategy", "caseId", "queryLatencyMs", "trustDecision"]
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({key: row.get(key) for key in fields})

if __name__ == "__main__": main()
