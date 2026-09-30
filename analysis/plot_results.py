from __future__ import annotations
import argparse, csv
from pathlib import Path

def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); args=ap.parse_args(); p=Path(args.input); rows=list(csv.DictReader((p/"comparison-summary.csv").open(encoding="utf-8"))); profiles=["static","semantic-only","trust-aware"]; faults=sorted({r["faultId"] for r in rows}); labels=["Static","Semantic-only","Trust-aware"]
    def draw(field,ylabel,stem):
        fig,ax=plt.subplots(figsize=(6.4,3.2)); width=.25; xs=list(range(len(faults)))
        for i,profile in enumerate(profiles):
            vals=[float(next((r[field] for r in rows if r["profile"]==profile and r["faultId"]==f),0)) for f in faults]; ax.bar([x+(i-1)*width for x in xs],vals,width,label=labels[i])
        ax.set_xticks(xs,[f.replace("-","\n") for f in faults],fontsize=7); ax.set_ylabel(ylabel); ax.grid(axis="y",alpha=.25); ax.legend(frameon=False,ncol=3,fontsize=8); fig.tight_layout(); fig.savefig(p/f"{stem}.pdf"); fig.savefig(p/f"{stem}.png",dpi=220); plt.close(fig)
    draw("meanRecall","Mean Recall","fig-recall"); draw("meanTrustedPrecision","Mean Trusted-Precision","fig-trusted-precision"); draw("meanInvalidExposure","Invalid-resource exposure","fig-invalid-exposure"); draw("meanQueryLatencyMs","Mean query latency (ms)","fig-query-latency"); draw("meanVerificationOverheadMs","Verification overhead (ms)","fig-verification-overhead")
if __name__=="__main__": main()
