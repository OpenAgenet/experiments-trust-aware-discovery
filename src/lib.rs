//! Explicit model of the OAN repositories used by the experiment.
//! Runtime HTTP calls remain in the TypeScript control-plane adapter so that
//! the experiment consumes public OAN APIs instead of vendoring core crates.
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
pub mod core_preflight;

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum CoreNode {
    Registrar,
    Root,
    CdnPublisher,
    Cdn,
    Discovery,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ControlPlaneEndpoint {
    pub node: CoreNode,
    pub repository: &'static str,
    pub base_url: &'static str,
    pub route: &'static str,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryLifecycle {
    pub stage: &'static str,
    pub node: CoreNode,
    pub route: &'static str,
    pub trust_evidence: &'static str,
}
pub fn control_plane_endpoints() -> [ControlPlaneEndpoint; 5] {
    [
        ControlPlaneEndpoint {
            node: CoreNode::Registrar,
            repository: "oan-registrar-node",
            base_url: "http://127.0.0.1:8101",
            route: "/resources/register",
        },
        ControlPlaneEndpoint {
            node: CoreNode::Root,
            repository: "oan-root-services/services/root-node",
            base_url: "http://127.0.0.1:8100",
            route: "/root/status",
        },
        ControlPlaneEndpoint {
            node: CoreNode::CdnPublisher,
            repository: "oan-root-services/services/cdn-publisher",
            base_url: "http://127.0.0.1:8110",
            route: "/publisher/status",
        },
        ControlPlaneEndpoint {
            node: CoreNode::Cdn,
            repository: "oan-root-services/services/cdn-node",
            base_url: "http://127.0.0.1:8105",
            route: "/resources",
        },
        ControlPlaneEndpoint {
            node: CoreNode::Discovery,
            repository: "oan-discovery-node/services/discovery-node",
            base_url: "http://127.0.0.1:8103",
            route: "/discovery/resources/query",
        },
    ]
}
pub fn discovery_lifecycle() -> [DiscoveryLifecycle; 5] {
    [
        DiscoveryLifecycle {
            stage: "registered",
            node: CoreNode::Registrar,
            route: "/resources/register",
            trust_evidence: "registrar identity and signed draft",
        },
        DiscoveryLifecycle {
            stage: "root-accepted",
            node: CoreNode::Root,
            route: "/root/status",
            trust_evidence: "Root package/version/hash validation",
        },
        DiscoveryLifecycle {
            stage: "cdn-published",
            node: CoreNode::CdnPublisher,
            route: "/publisher/status",
            trust_evidence: "published complete package",
        },
        DiscoveryLifecycle {
            stage: "discovery-indexed",
            node: CoreNode::Discovery,
            route: "/discovery/status",
            trust_evidence: "authorized package indexed",
        },
        DiscoveryLifecycle {
            stage: "query-observed",
            node: CoreNode::Discovery,
            route: "/discovery/resources/query",
            trust_evidence: "candidate plus lifecycle evidence",
        },
    ]
}
pub fn digest_registration_batch(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    format!("{:x}", h.finalize())
}
pub fn validate_counts(registered: u64, indexed: u64) -> Result<(), String> {
    if registered == 0 {
        return Err("empty registration batch".into());
    }
    if registered != indexed {
        return Err(format!(
            "discovery count mismatch: {registered} != {indexed}"
        ));
    }
    Ok(())
}

#[derive(Debug, Serialize)]
pub struct CoreTopology {
    pub registrar: &'static str,
    pub root: &'static str,
    pub cdn: &'static str,
    pub publisher: &'static str,
    pub discovery: &'static str,
    pub database: &'static str,
    pub trust_indexer: bool,
}
impl Default for CoreTopology {
    fn default() -> Self {
        Self {
            registrar: "oan-registrar-node",
            root: "oan-root-services/root-node",
            cdn: "oan-root-services/cdn-node",
            publisher: "oan-root-services/cdn-publisher",
            discovery: "oan-discovery-node/discovery-node",
            database: "sqlite",
            trust_indexer: false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn topology_has_nodes() {
        assert_eq!(control_plane_endpoints().len(), 5);
    }
    #[test]
    fn counts_fail_closed() {
        assert!(validate_counts(10, 10).is_ok());
        assert!(validate_counts(10, 9).is_err());
    }
}
