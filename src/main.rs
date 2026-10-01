use oan_discovery_experiment_tools::{control_plane_endpoints, discovery_lifecycle, CoreTopology};
fn main() {
    let report = serde_json::json!({"topology": CoreTopology::default(), "endpoints": control_plane_endpoints(), "lifecycle": discovery_lifecycle()});
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
}
