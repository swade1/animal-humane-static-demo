#!/usr/bin/env python3
"""
Alternative migration script using direct HTTP requests
"""
import json
import requests
from datetime import datetime

def main():
    print("🔄 Migrating Elasticsearch Data to Docker (HTTP Method)")
    print("=" * 55)
    
    # Test connections first
    try:
        print("🔍 Testing local Elasticsearch on port 9201...")
        local_response = requests.get("http://127.0.0.1:9201", timeout=10)
        if local_response.status_code == 200:
            print("✅ Connected to local Elasticsearch on port 9201")
        else:
            print(f"❌ Local Elasticsearch returned status {local_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to local Elasticsearch: {e}")
        return
    
    try:
        print("🔍 Testing Docker Elasticsearch on port 9200...")
        docker_response = requests.get("http://127.0.0.1:9200", timeout=10)
        if docker_response.status_code == 200:
            print("✅ Connected to Docker Elasticsearch on port 9200")
        else:
            print(f"❌ Docker Elasticsearch returned status {docker_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Docker Elasticsearch: {e}")
        return
    
    # Get indices from local
    try:
        print("\n📊 Getting indices from local Elasticsearch...")
        indices_response = requests.get("http://127.0.0.1:9201/_cat/indices?format=json", timeout=10)
        indices_data = indices_response.json()
        
        animal_indices = [idx["index"] for idx in indices_data if idx["index"].startswith("animal-humane-")]
        print(f"Found {len(animal_indices)} animal-humane indices:")
        for idx in sorted(animal_indices):
            print(f"   - {idx}")
            
        if not animal_indices:
            print("❌ No animal-humane indices found")
            return
            
    except Exception as e:
        print(f"❌ Failed to get indices: {e}")
        return
    
    # Migrate each index
    for index_name in animal_indices:
        try:
            print(f"\n🔄 Processing {index_name}...")
            
            # Check if index exists in Docker
            check_url = f"http://127.0.0.1:9200/{index_name}"
            check_response = requests.head(check_url, timeout=10)
            if check_response.status_code == 200:
                print(f"   ⚠️  Index {index_name} already exists in Docker, skipping")
                continue
                
            # Get mapping from source
            mapping_url = f"http://127.0.0.1:9201/{index_name}/_mapping"
            mapping_response = requests.get(mapping_url, timeout=10)
            mapping_data = mapping_response.json()
            
            # Create index in Docker
            create_body = {
                "mappings": mapping_data[index_name]["mappings"],
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }
            
            create_url = f"http://127.0.0.1:9200/{index_name}"
            create_response = requests.put(
                create_url, 
                json=create_body, 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if create_response.status_code not in [200, 201]:
                print(f"   ❌ Failed to create index: {create_response.text}")
                continue
                
            print(f"   ✅ Created index structure")
            
            # Get and copy documents
            search_url = f"http://127.0.0.1:9201/{index_name}/_search"
            search_body = {"query": {"match_all": {}}, "size": 1000}
            
            search_response = requests.post(
                search_url,
                json=search_body,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                hits = search_data["hits"]["hits"]
                
                if hits:
                    # Prepare bulk insert
                    bulk_data = []
                    for hit in hits:
                        bulk_data.append(json.dumps({"index": {"_index": index_name, "_id": hit["_id"]}}))
                        bulk_data.append(json.dumps(hit["_source"]))
                    
                    bulk_body = "\n".join(bulk_data) + "\n"
                    
                    # Insert into Docker
                    bulk_url = "http://127.0.0.1:9200/_bulk"
                    bulk_response = requests.post(
                        bulk_url,
                        data=bulk_body,
                        headers={"Content-Type": "application/x-ndjson"},
                        timeout=60
                    )
                    
                    if bulk_response.status_code == 200:
                        print(f"   ✅ Migrated {len(hits)} documents")
                    else:
                        print(f"   ❌ Failed to insert documents: {bulk_response.text}")
                else:
                    print(f"   ℹ️  No documents found in index")
            else:
                print(f"   ❌ Failed to search index: {search_response.text}")
                
        except Exception as e:
            print(f"   ❌ Error processing {index_name}: {e}")
            
    print(f"\n🎉 Migration completed!")

if __name__ == "__main__":
    main()