from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); args=ap.parse_args(); p=Path(args.input); rows=list(csv.DictReader((p/"query-summary.csv").open(encoding="utf-8"))); errors=[]
    for r in rows:
        for key in ("precision","recall","mrr","trustedPrecision","invalidExposure","queryLatencyMs","verificationOverheadMs"):
            try:
                if float(r[key])<0: raise ValueError("negative")
            except Exception as e: errors.append({"queryId":r.get("queryId",""),"error":f"{key}:{e}"})
    (p/"data-quality-errors.jsonl").write_text("".join(json.dumps(e)+"\n" for e in errors),encoding="utf-8")
    groups=defaultdict(list)
    for r in rows: groups[(r["profile"],r["faultId"])].append(r)
    out=[]
    for (profile,fault),items in sorted(groups.items()):
        n=len(items); avg=lambda k:sum(float(x[k]) for x in items)/n
        out.append({"profile":profile,"faultId":fault,"samples":n,"meanPrecision":avg("precision"),"meanRecall":avg("recall"),"meanMrr":avg("mrr"),"meanTrustedPrecision":avg("trustedPrecision"),"meanInvalidExposure":avg("invalidExposure"),"meanQueryLatencyMs":avg("queryLatencyMs"),"meanVerificationOverheadMs":avg("verificationOverheadMs")})
    fields=list(out[0]) if out else ["profile","faultId","samples"]
    with (p/"comparison-summary.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(out)
    (p/"analysis-manifest.json").write_text(json.dumps({"rawRows":len(rows),"groups":len(out),"dataQualityErrors":len(errors)},indent=2),encoding="utf-8"); print(json.dumps({"rawRows":len(rows),"groups":len(out),"dataQualityErrors":len(errors)},indent=2))
if __name__=="__main__": main()
