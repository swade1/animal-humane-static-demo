from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")
repository = "animal_humane_repo"
snapshot_name = "animal_humane_bulk_snapshot"

# Step 1: Create a snapshot for all indices
# List all indices if you want to be more selective:
indices = ",".join(es.indices.get_alias(index="*").keys())
snapshot_body = {
    "indices": indices,  # Use "_all" for all indices, or comma-separated names
    "include_global_state": False
}
es.snapshot.create(repository=repository, snapshot=snapshot_name, body=snapshot_body, wait_for_completion=True)

# Step 2: Restore all indices from the snapshot (can be selective as well)
restore_body = {
    "indices": indices,  # Or "_all"
    "include_global_state": False,
    "ignore_unavailable": True
}
es.snapshot.restore(repository=repository, snapshot=snapshot_name, body=restore_body, wait_for_completion=True)

