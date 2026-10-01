use oan_discovery_experiment_tools::validate_counts;
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::{env, fs, path::PathBuf};

#[derive(Deserialize)]
struct Manifest {
    mode: String,
    #[serde(rename = "registeredCount")]
    registered_count: u64,
    #[serde(rename = "discoveryIndexedCount")]
    discovery_indexed_count: u64,
    #[serde(rename = "trustIndexer")]
    trust_indexer: bool,
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = PathBuf::from(env::args().nth(1).ok_or("run directory required")?);
    let m: Manifest = serde_json::from_str(&fs::read_to_string(dir.join("run-manifest.json"))?)?;
    if m.mode != "real-oan-local" || m.trust_indexer {
        return Err("invalid real-run manifest".into());
    }
    validate_counts(m.registered_count, m.discovery_indexed_count)?;
    let data = fs::read(dir.join("registration-latency.json"))?;
    let mut h = Sha256::new();
    h.update(&data);
    println!(
        "validated mode={} resources={} registration_sha256={:x}",
        m.mode,
        m.registered_count,
        h.finalize()
    );
    Ok(())
}
