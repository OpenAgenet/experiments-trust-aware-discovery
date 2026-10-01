# Trust-Aware Semantic Discovery Experiments

This repository implements local, reproducible experiments for semantic resource discovery with lifecycle, version, authorization, package-integrity, and reachability checks. It builds an application-level experiment harness on top of existing OAN core services without copying or changing their production logic.

## OAN integration

The Rust crate has compile-time path dependencies on `oan-core`,
`oan-protocol`, and `oan-client` from the sibling `oan-protocol-common`
repository. `check_oan_core` validates the Root, Registrar, Discovery, and
protocol-common workspaces, required service binaries, SQLite support,
genesis identities, protocol constants, resource types, and live node health.
Every real run writes static and live preflight reports into its result
directory before resource registration proceeds.

The node lifecycle harness is repository-local. The topology generator under
`local-oan/scripts/` creates isolated genesis-based identities, configuration,
and SQLite databases. The local runtime starts Root, Registrar, CDN Publisher,
CDN, Discovery, and NATS; the local lifecycle observer waits for Root
acceptance, publication, and Discovery indexing. All experiment runtime code,
configuration templates, and lifecycle polling logic are maintained in this
repository; only the public OAN core repositories and `oan-design-docs`
genesis identities are external inputs.

Rust code under `src/` explicitly models the five OAN control-plane nodes,
their repositories, HTTP routes, and trust evidence. It also performs
fail-closed registered/indexed count checks, result hashing, CLI inspection,
and unit-tested manifest validation.

The executable integration path is visible in `ts-client/run-real.ts` and
`ts-client/src/core-integration.ts`. The runner uses the repository-local
harness to start the compiled `root-node`, `registrar-node`, `cdn-node`,
`cdn-publisher`, and `discovery-node` binaries, submits registrations to
`oan-registrar-node`, waits for Root acceptance and CDN publication, and then
queries `oan-discovery-node`. The generated manifest records this mapping in
`coreIntegration`.

| OAN component | Used capability | Repository responsibility |
|---|---|---|
| `oan-registrar-node` | Resource registration and registrar status APIs. | Generate typed fixtures and submit them through public HTTP endpoints. |
| Root node in `oan-root-services` | Resource-package validation, version/lifecycle handling, authorization evidence, and publication state. | Observe results and provide controlled valid or invalid inputs; never bypass or replace Root decisions. |
| CDN node and publisher | Package storage, index publication, and package retrieval. | Measure publication/fetch timing and inject only local fixture/proxy faults. |
| `oan-discovery-node` | Authorized-resource synchronization, indexing, structured/semantic query, explanations, visibility, and rejection diagnostics. | Supply query sets and gold labels, execute comparison profiles, and analyze candidates. |
| `oan-protocol-common` | Shared resource, package, credential, hash, and protocol contracts. | Consume public contracts and record the referenced commit; do not vendor core crates. |
| `oan-sdk-ts` | `OanClient`, resource draft helpers, lifecycle observation, package/candidate checks, and trust summaries. | Implement typed client workflows and experiment-specific validation orchestration. |
| SQLite and NATS | Local dependencies of OAN core services. | The real runner creates isolated SQLite files and uses NATS JetStream only for Root-to-CDN publication; it never writes directly to core databases. |

Discovery candidates are not treated as complete authorization. The trust-aware profile fetches a complete Root/CDN package before applying package, lifecycle, version, binding, and artifact checks.

Trust Indexer is not used. Existing local genesis identities and authorization material are supplied through configuration. This repository does not issue infrastructure authorization, fabricate Root proof, or insert records directly into Discovery.

## Comparison profiles

- `static`: deterministic type/name lookup without semantic ranking or a trust gate.
- `semantic-only`: Discovery semantic ranking without complete package validation.
- `trust-aware`: semantic ranking followed by complete-package retrieval and eligibility filtering.

All profiles use the same resources, query set, random seed, network profile, core-service instances, and repetitions.

## Language responsibilities

- TypeScript: OAN HTTP access, typed drafts, lifecycle observation, package validation, query execution, and JSONL event serialization.
- Python: run orchestration, repetition, fault schedules, data-quality checks, and offline aggregation.
- Rust: optional typed fixture, digest, proxy, or high-throughput helper tools.

## Real local run

The supported experiment path starts an isolated local Root, Registrar, CDN,
CDN Publisher, and Discovery topology with genesis identities, SQLite files,
and NATS JetStream. Trust Indexer remains disabled. The runner fails on an
unavailable service and never falls back to an emulation result.

```text
npm install
$env:OAN_WORKSPACE_ROOT="D:\\Works\\VscodeProject\\OAN"
$env:OAN_NATS_SERVER_PATH="C:\\Program Files\\WinGet\\Links\\nats-server.exe"
$env:OAN_DISCOVERY_RESOURCES="200"
npm run run:real -- --output results/real-oan-local-200
python analysis/analyze_real.py --input results/real-oan-local-200
```

The runner registers resources through Registrar, waits for Root acceptance,
NATS publication, CDN persistence, and Discovery indexing, then executes real
Discovery queries. It records `mode=real-oan-local`, `databaseBackend=sqlite`,
and `trustIndexer=false` in the manifest.

## Configuration

Copy `configs/local.sample.json` to `configs/local.json` and replace every placeholder port with the actual local endpoint. Core services must already be running. The repository does not start, reset, or reconfigure core databases.

The comparison switches are defined in `configs/comparison-profiles.json`.

## Commands

```text
npm install
npm run probe -- --config configs/local.json
npm run run:discovery -- --config configs/local.json
npm run analyze:real -- --input results/real-oan-local-200
```

## Outputs

A complete run produces capability probes, a run manifest, JSONL event/lifecycle/query traces, fixed expected labels, derived CSV files, data-quality errors, and checksums. Generated results belong under `results/<run-id>/`; secrets, private keys, production credentials, and external server addresses must not be committed.

The experiment measures local software-control-plane behavior only. It does not represent real orbital, radio, satellite-power, or blockchain-governance performance.
