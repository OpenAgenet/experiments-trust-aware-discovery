# Trust-Aware Semantic Discovery Experiments

This repository implements local, reproducible experiments for semantic resource discovery with lifecycle, version, authorization, package-integrity, and reachability checks. It builds an application-level experiment harness on top of existing OAN core services without copying or changing their production logic.

## OAN integration

| OAN component | Used capability | Repository responsibility |
|---|---|---|
| `oan-registrar-node` | Resource registration and registrar status APIs. | Generate typed fixtures and submit them through public HTTP endpoints. |
| Root node in `oan-root-services` | Resource-package validation, version/lifecycle handling, authorization evidence, and publication state. | Observe results and provide controlled valid or invalid inputs; never bypass or replace Root decisions. |
| CDN node and publisher | Package storage, index publication, and package retrieval. | Measure publication/fetch timing and inject only local fixture/proxy faults. |
| `oan-discovery-node` | Authorized-resource synchronization, indexing, structured/semantic query, explanations, visibility, and rejection diagnostics. | Supply query sets and gold labels, execute comparison profiles, and analyze candidates. |
| `oan-protocol-common` | Shared resource, package, credential, hash, and protocol contracts. | Consume public contracts and record the referenced commit; do not vendor core crates. |
| `oan-sdk-ts` | `OanClient`, resource draft helpers, lifecycle observation, package/candidate checks, and trust summaries. | Implement typed client workflows and experiment-specific validation orchestration. |
| PostgreSQL and NATS | Local dependencies of OAN core services. | Probe availability and record versions; never write directly to core databases. |

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

## Configuration

Copy `configs/local.sample.json` to `configs/local.json` and replace every placeholder port with the actual local endpoint. Core services must already be running. The repository does not start, reset, or reconfigure core databases.

The comparison switches are defined in `configs/comparison-profiles.json`.

## Commands

```text
npm install
npm run probe -- --config configs/local.json
npm run run:discovery -- --config configs/local.json
uv run python -m runners.batch --input results/<run-id> --output results/<run-id>/derived
```

## Outputs

A complete run produces capability probes, a run manifest, JSONL event/lifecycle/query traces, fixed expected labels, derived CSV files, data-quality errors, and checksums. Generated results belong under `results/<run-id>/`; secrets, private keys, production credentials, and external server addresses must not be committed.

The experiment measures local software-control-plane behavior only. It does not represent real orbital, radio, satellite-power, or blockchain-governance performance.
