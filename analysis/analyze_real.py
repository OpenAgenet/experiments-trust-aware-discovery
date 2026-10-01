"""Aggregate real local OAN discovery results and generate paper figures."""
from __future__ import annotations
import argparse, json, statistics
from pathlib import Path
import matplotlib.pyplot as plt

def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--input", required=True); args = ap.parse_args()
    p = Path(args.input)
    manifest = json.loads((p / "run-manifest.json").read_text(encoding="utf-8"))
    registrations = json.loads((p / "registration-latency.json").read_text(encoding="utf-8"))
    queries = json.loads((p / "query-results.json").read_text(encoding="utf-8"))
    lat = [float(x["registrationLatencyMs"]) for x in registrations]
    qlat = [float(x["latencyMs"]) for x in queries]
    summary = {"mode": manifest["mode"], "databaseBackend": manifest.get("databaseBackend", "sqlite"), "resourceCount": len(registrations), "registeredCount": manifest["registeredCount"], "discoveryIndexedCount": manifest["discoveryIndexedCount"], "registrationMeanMs": statistics.mean(lat), "registrationP95Ms": sorted(lat)[max(0, int(len(lat)*.95)-1)], "queryMeanMs": statistics.mean(qlat), "queryP95Ms": sorted(qlat)[max(0, int(len(qlat)*.95)-1)], "queryCount": len(queries)}
    (p / "paper-metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    plt.figure(figsize=(5.8, 3.3)); plt.plot(range(1, len(lat)+1), lat, linewidth=.7); plt.xlabel("Registered resource"); plt.ylabel("Registration latency (ms)"); plt.title("Local registration latency"); plt.tight_layout(); plt.savefig(p/"registration-latency.png", dpi=220); plt.savefig(p/"registration-latency.pdf"); plt.close()
    plt.figure(figsize=(5.8, 3.3)); labels=[x["query"][:18] for x in queries]; plt.bar(range(len(qlat)), qlat, color="#4472C4"); plt.xticks(range(len(qlat)), labels, rotation=25, ha="right", fontsize=7); plt.ylabel("Discovery query latency (ms)"); plt.title("Local Discovery query latency"); plt.tight_layout(); plt.savefig(p/"discovery-query-latency.png", dpi=220); plt.savefig(p/"discovery-query-latency.pdf"); plt.close()
    print(json.dumps(summary, indent=2))
if __name__ == "__main__": main()
