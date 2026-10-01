import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { assertRealManifest, lifecycleStages } from "./src/real-client.ts";
import { integrationSummary } from "./src/core-integration.ts";

const experimentRoot = path.resolve(process.cwd());
const root = path.resolve(process.env.OAN_CORE_SOURCES_ROOT ?? path.resolve(experimentRoot, ".."));
process.env.OAN_WORKSPACE_ROOT = root;
const localOan = path.join(experimentRoot, "local-oan");
const shared: any = await import(pathToFileURL(path.join(localOan, "scripts", "bench", "runtime.ts")).href);
const flows: any = await import(pathToFileURL(path.join(localOan, "scripts", "bench", "lifecycle.ts")).href);
const outputIndex = process.argv.indexOf("--output");
const positional = process.argv.slice(2).find((value) => !value.startsWith("-"));
const out = path.resolve(outputIndex >= 0 && process.argv[outputIndex + 1] ? process.argv[outputIndex + 1] : (positional ?? "results/real-oan-local"));
console.log(`experiment lifecycle: ${lifecycleStages().join(" -> ")}`);
const count = Number(process.env.OAN_DISCOVERY_RESOURCES ?? "200");
const profile = process.env.OAN_DISCOVERY_PROFILE ?? "trust-aware";
if (!["static", "semantic-only", "trust-aware"].includes(profile)) throw new Error("OAN_DISCOVERY_PROFILE must be static, semantic-only, or trust-aware");
const runStamp = Date.now().toString();
const work = path.join(localOan, ".local-oan-topology", runStamp);
const pidDir = path.join(localOan, ".local-oan-pids", runStamp);
fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true }); fs.rmSync(pidDir, { recursive: true, force: true }); fs.mkdirSync(pidDir, { recursive: true });
  execFileSync("node", [path.join(localOan, "scripts", "generate-local-topology.mjs")], { cwd: localOan, stdio: "inherit", env: { ...process.env, OAN_WORKSPACE_ROOT: root, OAN_EXPERIMENT_ROOT: localOan, OAN_LOCAL_TOPOLOGY_ROOT: work } });
  localizeTopologyPaths(work, root);
for (const file of fs.readdirSync(work, { recursive: true })) { if (String(file).endsWith(".toml")) { const p = path.join(work, String(file)); let cfg = fs.readFileSync(p, "utf8"); const dir = path.dirname(p); const name = path.basename(dir); const dbPath = path.join(dir, `${name}.db`).replace(/\\/g, "/"); cfg = cfg.replace(/database_url\s*=\s*"[^"]*"/g, `database_url = "sqlite:${dbPath}"`); fs.writeFileSync(p, cfg, "utf8"); } }
const event = shared.uniqueRootEventStreamProfile(`paper1-${Date.now()}`, 4222);
const rootConfig = path.join(work, "root", "config.example.toml");
let text = fs.readFileSync(rootConfig, "utf8").replace(/\[events\][\s\S]*$/m, "");
text += `\n[events]\nenabled = true\nbackend = "${event.backend}"\nendpoint = "${event.endpoint}"\nstream = "${event.stream}"\ncdn_publish_subject = "${event.cdnPublishSubject}"\npublish_timeout_ms = 1000\nfailure_mode = "closed"\n`;
fs.writeFileSync(rootConfig, text, "utf8");
shared.writeBenchmarkCdnPublisherConfig(path.join(work, "cdn-publisher", "config.example.toml"), { publisherPort: 8110, rootPort: 8100, cdnPort: 8105 }, { events: event, rootKeysDirRelative: "../root/keys" });
shared.ensureServiceBinaries(["root-node", "registrar-node", "discovery-node", "cdn-node", "cdn-publisher"]); runCorePreflight(false, path.join(out, "oan-core-preflight-static.json"));
const nats = shared.createNatsRuntime(pidDir); const nodes = [
  shared.createNodeRuntime(pidDir,"root","root-node",rootConfig,8100), shared.createNodeRuntime(pidDir,"registrar","registrar-node",path.join(work,"registrar-a/config.example.toml"),8101), shared.createNodeRuntime(pidDir,"discovery","discovery-node",path.join(work,"discovery-a/config.example.toml"),8103), shared.createNodeRuntime(pidDir,"cdn","cdn-node",path.join(work,"cdn/config.example.toml"),8105), shared.createNodeRuntime(pidDir,"publisher","cdn-publisher",path.join(work,"cdn-publisher/config.example.toml"),8110)
];
const started: any[] = [];
try {
  await shared.startNats(nats, 4222); await shared.startNodesInPhases(nodes); started.push(...nodes); runCorePreflight(true, path.join(out, "oan-core-preflight-live.json"));
  const registrar = shared.loadIdentityMaterial(path.join(work,"registrar-a")); const rootUrl="http://127.0.0.1:8100", regUrl="http://127.0.0.1:8101", discUrl="http://127.0.0.1:8103";
  const rows: any[] = []; const events: any[] = []; const startedAt = Date.now();
  for (let i=0;i<count;i++) {
    const identity = shared.createResourceIdentity({ semanticCode: i%4===0?"SKDM":i%4===1?"MCDM":i%4===2?"TLDM":"AGDM", resourceType: i%4===0?"skill":i%4===1?"mcp_server":i%4===2?"tool_api":"agent_service", capabilityTags:["satellite.earth_observation", i%2?"edge.anomaly_detection":"edge.cloud_detection"], serviceEndpoint:`http://127.0.0.1:9900/resource/${i}`, label:`Satellite resource ${i}`, description:`Local satellite edge resource for ${i%2?"anomaly detection":"cloud detection"}`, protocol:"http", serviceType:"AgentService"});
    const fixture = shared.buildResourceRegistrationFixture(identity,{draftId:`paper1-${i}`,registrarDid:registrar.did,resourceType:identity.didDocument.oanMetadata.resourceType,metadata:{source:"paper1-real-oan"}});
    const t0=Date.now(); await shared.postJson(`${regUrl}/resources/register`,fixture,{timeoutMs:120000}); rows.push({resourceIndex:i,registrationLatencyMs:Date.now()-t0,did:identity.did}); events.push({stage:"registered",resourceIndex:i,timestamp:new Date().toISOString()});
  }
  await shared.waitForRootLatestVersionCount(rootUrl,count,600000); await flows.waitForRootEventPublish(rootUrl,count,600000); await flows.waitForPublisherAck("http://127.0.0.1:8110",count,600000); await flows.waitForCdnResourceCount("http://127.0.0.1:8105",count,600000); const sync=await flows.waitForDiscoveryIndexedCount(discUrl,count,600000);
  const queries=["cloud detection satellite edge service","anomaly detection satellite edge service","earth observation telemetry resource","edge computing resource"];
  const queryRows:any[]=[]; for (let rep=0;rep<5;rep++) for (const q of queries) { const t0=Date.now(); const request = profile === "static" ? {query:"",limit:10} : {query:q,limit:10}; const response=await shared.postJson(`${discUrl}/discovery/resources/query`,request); let candidates=response.candidates??response.items??[]; let packageChecks=0; if (profile === "trust-aware") { for (const candidate of candidates.slice(0, 3)) { const did=encodeURIComponent(candidate.resourceDid ?? candidate.resource_did ?? ""); if (!did) continue; const packageResponse=await fetch(`http://127.0.0.1:8105/cdn/resources/${did}`); if (packageResponse.ok) packageChecks++; } } if (profile === "static") candidates=[...candidates].sort((a:any,b:any)=>String(a.resourceDid??a.resource_did).localeCompare(String(b.resourceDid??b.resource_did))); queryRows.push({repetition:rep,query:q,profile,latencyMs:Date.now()-t0,candidateCount:candidates.length,packageChecks,mode:"real-oan-local"}); }
  const manifest={runId:`paper1-${profile}-${Date.now()}`,profile,mode:"real-oan-local",coreEndpointMode:"connected",databaseBackend:"sqlite",trustIndexer:false,coreIntegration:integrationSummary(),resourceCount:count,registeredCount:rows.length,discoveryIndexedCount:sync.indexedResourceCount,registrarEndpoint:regUrl,rootEndpoint:rootUrl,discoveryEndpoint:discUrl,cdnEndpoint:"http://127.0.0.1:8105",generatedAt:new Date().toISOString()};
  fs.writeFileSync(path.join(out,"run-manifest.json"),JSON.stringify(manifest,null,2)); fs.writeFileSync(path.join(out,"registration-latency.json"),JSON.stringify(rows)); fs.writeFileSync(path.join(out,"query-results.json"),JSON.stringify(queryRows,null,2)); fs.writeFileSync(path.join(out,"events.jsonl"),events.map(x=>JSON.stringify(x)).join("\n")+"\n"); assertRealManifest(manifest); console.log(JSON.stringify(manifest,null,2));
 } finally { for (const n of [...started].reverse()) await shared.stopNode(n); await shared.stopNats(nats); }

function localizeTopologyPaths(topology: string, workspace: string): void {
  for (const file of fs.readdirSync(topology, { recursive: true })) {
    if (!String(file).endsWith(".toml")) continue;
    const p = path.join(topology, String(file)); let text = fs.readFileSync(p, "utf8");
    text = text.replaceAll("\\", "/");
    text = text.replaceAll("../../.oan-multi-node-demo", topology.replaceAll("\\", "/"));
    text = text.replaceAll("../../docs/capability-tree-v1.json", path.join(workspace, "oan-design-docs/docs/capability-tree-v1.json").replaceAll("\\", "/")); fs.writeFileSync(p, text, "utf8");
  }
}

function runCorePreflight(live: boolean, output: string): void {
  execFileSync("cargo", ["run", "--quiet", "--bin", "check_oan_core", "--", ...(live ? ["--live"] : []), "--output", output], {
    cwd: experimentRoot,
    stdio: "inherit",
    env: { ...process.env, OAN_WORKSPACE_ROOT: root },
    windowsHide: true,
  });
}
