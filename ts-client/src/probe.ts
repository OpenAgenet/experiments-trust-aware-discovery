import { readFile } from "node:fs/promises";
import { OanClient } from "@openagenet/oan-sdk-ts/client";

type Config = { endpoints: Record<string, string> };
const index = process.argv.indexOf("--config");
const configPath = index >= 0 ? process.argv[index + 1] : undefined;
if (!configPath) throw new Error("--config is required");
const config = JSON.parse(await readFile(configPath, "utf8")) as Config;
const e = config.endpoints;
const client = new OanClient({ registrarEndpoint: e.registrar, rootEndpoint: e.root, cdnEndpoint: e.cdn, discoveryEndpoint: e.discovery });
const probes: Record<string, unknown> = {};
for (const [name, url] of Object.entries(e)) {
  const started = performance.now();
  if (url.includes("_PORT")) { probes[name] = { status: "not-configured" }; continue; }
  try { const response = await fetch(`${url}/health`); probes[name] = { status: response.ok ? "supported" : "failed", httpStatus: response.status, latencyMs: performance.now() - started }; }
  catch (error) { probes[name] = { status: "failed", error: String(error), latencyMs: performance.now() - started }; }
}
probes.registrarStatus = await client.getRegistrarStatus().then((value) => ({ status: "supported", value })).catch((error) => ({ status: "failed", error: String(error) }));
console.log(JSON.stringify({ generatedAt: new Date().toISOString(), probes }, null, 2));
