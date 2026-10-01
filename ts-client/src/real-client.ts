export type EndpointSet={registrar:string;root:string;cdn:string;discovery:string};
export async function health(endpoint:string):Promise<boolean>{const r=await fetch(`${endpoint}/health`);return r.ok;}
export async function requireTopology(e:EndpointSet):Promise<void>{for(const [name,url] of Object.entries(e)){if(!(await health(url)))throw new Error(`${name} unavailable: ${url}`);}}
export function lifecycleStages(){return ["registered","root-accepted","cdn-published","discovery-indexed"] as const;}
export function assertRealManifest(m:Record<string,unknown>){if(m.mode!=="real-oan-local"||m.databaseBackend!=="sqlite"||m.trustIndexer!==false)throw new Error("not a real SQLite OAN run");}
