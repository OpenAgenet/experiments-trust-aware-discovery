import { readFile } from "node:fs/promises";
import { OanClient } from "@openagenet/oan-sdk-ts/client";

const index = process.argv.indexOf("--config");
const configPath = index >= 0 ? process.argv[index + 1] : undefined;
if (!configPath) throw new Error("--config is required");
const config = JSON.parse(await readFile(configPath, "utf8")) as { endpoints: Record<string, string>; query?: Record<string, unknown> };
const client = new OanClient({ registrarEndpoint: config.endpoints.registrar, rootEndpoint: config.endpoints.root, cdnEndpoint: config.endpoints.cdn, discoveryEndpoint: config.endpoints.discovery });
const query = config.query ?? { query: "edge cloud detection", resourceType: "skill", limit: 10 };
const started = performance.now();
const response = await client.discoverResources(query as Parameters<OanClient["discoverResources"]>[0]);
console.log(JSON.stringify({ stage: "query-finished", query, latencyMs: performance.now() - started, candidates: response.candidates }, null, 2));
