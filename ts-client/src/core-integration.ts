/** Explicit integration map for the local OAN control plane.
 * The implementation is provided by the official repositories; this module
 * keeps the experiment's dependency surface visible and typed.
 */
export const OAN_CORE_REPOSITORIES = {
  registrar: "oan-registrar-node",
  root: "oan-root-services/services/root-node",
  cdn: "oan-root-services/services/cdn-node",
  publisher: "oan-root-services/services/cdn-publisher",
  discovery: "oan-discovery-node/services/discovery-node",
  sdk: "oan-sdk-ts",
} as const;
export const LOCAL_OAN_ENDPOINTS = { registrar: "http://127.0.0.1:8101", root: "http://127.0.0.1:8100", cdn: "http://127.0.0.1:8105", publisher: "http://127.0.0.1:8110", discovery: "http://127.0.0.1:8103" } as const;
export type OanLifecycleStage = "registered" | "root-accepted" | "cdn-published" | "discovery-indexed";
export const OAN_LIFECYCLE: readonly OanLifecycleStage[] = ["registered", "root-accepted", "cdn-published", "discovery-indexed"];
export const OAN_ROUTES = { register: "/resources/register", rootStatus: "/root/status", discoveryQuery: "/discovery/resources/query", discoveryStatus: "/discovery/status" } as const;
export function integrationSummary() { return { repositories: OAN_CORE_REPOSITORIES, endpoints: LOCAL_OAN_ENDPOINTS, lifecycle: OAN_LIFECYCLE, routes: OAN_ROUTES, database: "sqlite", trustIndexer: false }; }
