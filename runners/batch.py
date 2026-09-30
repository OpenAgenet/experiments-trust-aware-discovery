"""Deterministic local harness for trust-aware semantic discovery."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, random, sys, time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROFILES = ("static", "semantic-only", "trust-aware")
FAULTS = ("none", "inactive", "revoked", "unauthorized", "hash-mismatch", "unreachable", "superseded")
CAPABILITIES = (("cloud detection", "skill"), ("target classification", "mcp_server"), ("anomaly detection", "tool_api"), ("telemetry access", "agent_service"))

def iso() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def digest(value: Any) -> str: return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def words(text: str) -> set[str]: return set(text.lower().replace("-", " ").split())

@dataclass(frozen=True)
class Resource:
    family: str; resource_type: str; did: str; name: str; description: str; version: str; lifecycle: str; authorized: bool; reachable: bool; package_hash: str; metadata_hash: str

def make_resources(count: int) -> list[Resource]:
    out=[]
    for i in range(count):
        capability, rtype = CAPABILITIES[i % len(CAPABILITIES)]; family=f"svc-{i//2:03d}"; version="1.1.0" if i % 2 else "1.0.0"; desc=f"edge satellite {capability} service for Earth observation"
        meta=digest({"family":family,"type":rtype,"version":version,"description":desc}); pkg=digest({"meta":meta,"endpoint":f"mock://service/{i}"}); code="SKDM" if rtype=="skill" else "MCDM" if rtype=="mcp_server" else "TLDM" if rtype=="tool_api" else "AGDM"
        out.append(Resource(family,rtype,f"did:oan:{code}:{i+1:032d}",f"{capability} service {i}",desc,version,"active",True,True,pkg,meta))
    return out

def alter(r: Resource, fault: str) -> Resource:
    x=asdict(r)
    if fault=="inactive": x["lifecycle"]="inactive"
    if fault=="revoked": x["lifecycle"]="revoked"
    if fault=="unauthorized": x["authorized"]=False
    if fault=="hash-mismatch": x["package_hash"]="sha256:"+"0"*64
    if fault=="unreachable": x["reachable"]=False
    if fault=="superseded": x["version"]="0.9.0"
    return Resource(**x)

def query_for(r: Resource) -> str: return f"find an edge service for {r.description.split(' for ')[0]} in an Earth observation task"

def run_query(profile: str, query: str, base: list[Resource], fault: str, k: int, rng: random.Random, qid: str) -> tuple[dict[str,Any], list[dict[str,Any]]]:
    qwords=words(query); capability=next((cap for cap,_ in CAPABILITIES if cap in query), "cloud detection"); matching=[r for r in base if capability in r.description]; target=matching[0].family if matching else base[0].family; candidates=[]; events=[]; resources=[]; altered_once=False
    for r in base:
        if fault!="none" and not altered_once and r.family==target:
            resources.append(alter(r,fault)); altered_once=True
        else: resources.append(r)
    for r in resources:
        overlap=len(qwords & words(r.description)); capability_hit=1.0 if capability in r.description else 0.0; semantic=(overlap/max(1,len(qwords))) + capability_hit; static=(1.0 if r.resource_type in ("skill","mcp_server") else 0.4) + 0.01*(99-int(r.did.rsplit(':',1)[-1])); score=static if profile=="static" else semantic + rng.random()*0.02; candidates.append((score,r,semantic))
    candidates.sort(key=lambda x:(-x[0],x[1].did)); top=candidates[:k]; selected=[]; invalid=0; reasons=[]; validation_ms=0.0
    for _,r,_ in top:
        eligible=True; reason="eligible"
        if profile=="trust-aware":
            validation_ms += 0.25 + rng.random()*0.1
            if r.lifecycle!="active": eligible=False; reason="lifecycle"
            elif not r.authorized: eligible=False; reason="authorization"
            elif not r.reachable: eligible=False; reason="unreachable"
            elif r.package_hash.startswith("sha256:0000"): eligible=False; reason="hash"
            elif r.version=="0.9.0": eligible=False; reason="superseded"
        if eligible: selected.append(r.did)
        else: invalid += 1; reasons.append(reason)
    relevant={r.did for r in resources if capability in r.description and r.lifecycle=="active" and r.authorized and r.reachable and r.version!="0.9.0"}; returned=set(selected); precision=len(returned&relevant)/max(1,len(returned)); recall=len(returned&relevant)/max(1,len(relevant)); invalid_exposure=invalid/max(1,len(top)); latency=0.8+(0.4 if profile!="static" else 0.0)+validation_ms
    row={"queryId":qid,"profile":profile,"faultId":fault,"k":k,"precision":round(precision,6),"recall":round(recall,6),"mrr":round(1.0 if any(r.did in selected for r in resources if capability in r.description) else 0.0,6),"trustedPrecision":round(precision,6),"invalidExposure":round(invalid_exposure,6),"queryLatencyMs":round(latency,4),"verificationOverheadMs":round(validation_ms,4),"candidateCount":len(top),"eligibleCount":len(selected),"rejectionReasons":";".join(reasons)}
    for stage in ("query-started","candidate-ranked","trust-filtered","query-finished"): events.append({"runId":"pending","queryId":qid,"profile":profile,"faultId":fault,"stage":stage,"candidateDids":selected,"timestamp":iso(),"latencyMs":row["queryLatencyMs"],"trustDecision":"eligible" if profile=="trust-aware" else "unverified"})
    return row,events

def write_csv(path:Path, rows:list[dict[str,Any]], fields:list[str]):
    with path.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows({f:r.get(f,"") for f in fields} for r in rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",required=True); ap.add_argument("--output"); ap.add_argument("--repetitions",type=int); args=ap.parse_args(); cfg=json.loads(Path(args.config).read_text(encoding="utf-8")); seed=int(cfg.get("seed",20261001)); reps=args.repetitions or int(cfg.get("scale",{}).get("repetitions",3)); rng=random.Random(seed); run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-local-emulation"; out=Path(args.output) if args.output else Path("results")/run_id; out.mkdir(parents=True,exist_ok=True); base=make_resources(int(cfg.get("scale",{}).get("resourceCount",100))); queries=[query_for(r) for r in base[:min(20,len(base))]]; rows=[]; events=[]; profiles=tuple(cfg.get("profiles",PROFILES)); faults=tuple(cfg.get("faults",FAULTS))
    for rep in range(reps):
        for qi,q in enumerate(queries):
            for profile in profiles:
                for fault in faults:
                    row,ev=run_query(profile,q,base,fault,5,rng,f"r{rep:02d}-q{qi:03d}-{profile}-{fault}"); row.update({"runId":run_id,"repetition":rep,"resourceCount":len(base),"queryText":q}); rows.append(row)
                    for e in ev: e.update({"runId":run_id,"repetition":rep}); events.append(e)
    manifest={"runId":run_id,"mode":"local-harness-emulation","seed":seed,"repetitions":reps,"resourceCount":len(base),"queryCount":len(queries),"profiles":profiles,"faults":faults,"coreEndpointMode":"not-connected","trustIndexer":False,"generatedAt":iso(),"python":sys.version,"platform":platform.platform()}; (out/"run-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    with (out/"events.jsonl").open("w",encoding="utf-8") as h:
        for e in events: h.write(json.dumps(e,separators=(",",":"))+"\n")
    fields=["runId","repetition","queryId","profile","faultId","resourceCount","k","precision","recall","mrr","trustedPrecision","invalidExposure","queryLatencyMs","verificationOverheadMs","candidateCount","eligibleCount","rejectionReasons","queryText"]; write_csv(out/"query-summary.csv",rows,fields); write_csv(out/"discovery-metrics.csv",rows,["profile","faultId","precision","recall","mrr","trustedPrecision","invalidExposure","queryLatencyMs","verificationOverheadMs"]); print(json.dumps({"runId":run_id,"output":str(out),"rows":len(rows),"events":len(events),"mode":manifest["mode"]},indent=2))

if __name__=="__main__": main()
