from __future__ import annotations
import argparse, json, statistics
from pathlib import Path

def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); args = ap.parse_args()
    root = Path(args.root); profiles = ["static", "semantic-only", "trust-aware"]
    rows = []
    for profile in profiles:
        data = json.loads((root / f"real-oan-rust-core-{profile}" / "paper-metrics.json").read_text(encoding="utf-8"))
        rows.append({"profile": profile, "registrationMeanMs": data["registrationMeanMs"], "registrationP95Ms": data["registrationP95Ms"], "queryMeanMs": data["queryMeanMs"], "queryP95Ms": data["queryP95Ms"], "registeredCount": data["registeredCount"], "indexedCount": data["discoveryIndexedCount"]})
    out = root / "comparison-summary.json"; out.write_text(json.dumps({"profiles": rows, "pairedQueries": 20, "resourceCount": 200}, indent=2), encoding="utf-8")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        labels = ["Static", "Semantic-only", "Trust-aware"]
        latency = [r["queryMeanMs"] for r in rows]
        fig, ax = plt.subplots(figsize=(5.8, 3.2)); ax.bar(labels, latency, color=["#7F7F7F", "#4472C4", "#70AD47"]); ax.set_ylabel("Mean query latency (ms)"); ax.set_title("Discovery profile comparison"); ax.grid(axis="y", alpha=.25); fig.tight_layout(); fig.savefig(root / "comparison-query-latency.pdf"); fig.savefig(root / "comparison-query-latency.png", dpi=220); plt.close(fig)
    except ImportError:
        pass
if __name__ == "__main__": main()
