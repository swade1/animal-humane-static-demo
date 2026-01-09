import argparse
from elasticsearch import Elasticsearch, helpers

# Usage: python migrate_specific_indices_by_gpt4.py --source-port 9201 --dest-port 9200 --indices animal-humane-20260102-1742,animal-humane-20260102-0900

def migrate_index(source_es, dest_es, index_name):
    print(f"Migrating index: {index_name}")
    # Scan all docs from source index
    docs = helpers.scan(source_es, index=index_name)
    actions = []
    for doc in docs:
        action = {
            "_op_type": "index",
            "_index": index_name,
            "_id": doc['_id'],
            "_source": doc['_source']
        }
        actions.append(action)
    if actions:
        helpers.bulk(dest_es, actions)
        print(f"✅ Migrated {len(actions)} docs to {index_name}")
    else:
        print(f"⚠️ No docs found in {index_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate specific Elasticsearch indices from source to destination.")
    parser.add_argument('--source-port', type=int, default=9201, help='Source Elasticsearch port')
    parser.add_argument('--dest-port', type=int, default=9200, help='Destination Elasticsearch port')
    parser.add_argument('--indices', type=str, required=True, help='Comma-separated list of indices to migrate')
    args = parser.parse_args()

    source_es = Elasticsearch(f"http://localhost:{args.source_port}")
    dest_es = Elasticsearch(f"http://localhost:{args.dest_port}")

    indices = [idx.strip() for idx in args.indices.split(",") if idx.strip()]
    for index_name in indices:
        migrate_index(source_es, dest_es, index_name)

    print("Migration complete.")
