from elasticsearch import Elasticsearch

es2 = Elasticsearch("http://localhost:9200")
repository = "usb_snapshot_repo"
snapshot_name = "all_indices_snapshot"

# Optionally list available snapshots to verify
snapshots = es2.snapshot.get(repository=repository, snapshot="_all")
print(f"Available snapshots: {[s['snapshot'] for s in snapshots['snapshots']]}")

# Restore all indices and global cluster state from snapshot
es2.snapshot.restore(
    repository=repository,
    snapshot=snapshot_name,
    body={"indices": "_all", "include_global_state": True, "ignore_unavailable": True},
    wait_for_completion=True
)

print("Restore completed successfully.")

