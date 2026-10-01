import argparse,json,statistics
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('input'); p=Path(ap.parse_args().input); m=json.loads((p/'run-manifest.json').read_text()); r=json.loads((p/'registration-latency.json').read_text()); q=json.loads((p/'query-results.json').read_text()); out={'real':m['mode']=='real-oan-local' and m.get('databaseBackend','sqlite')=='sqlite','resources':len(r),'registration':{'mean':statistics.mean(x['registrationLatencyMs'] for x in r),'p95':sorted(x['registrationLatencyMs'] for x in r)[int(len(r)*.95)-1]},'queries':{'count':len(q),'mean':statistics.mean(x['latencyMs'] for x in q)}}; (p/'report.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
