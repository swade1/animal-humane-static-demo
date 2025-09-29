#!/usr/bin/env python3
"""
Migrate existing Elasticsearch data to Docker container
"""
import json
import requests
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, bulk

def main():
    print("🔄 Migrating Elasticsearch Data to Docker")
    print("=" * 45)
    
    # Source: Your local Elasticsearch on port 9201
    print("🔍 Connecting to local Elasticsearch on port 9201...")
    local_es = Elasticsearch("http://localhost:9201")
    
    # Target: Docker Elasticsearch on port 9200
    print("🔍 Connecting to Docker Elasticsearch on port 9200...")
    docker_es = Elasticsearch("http://localhost:9200")
    
    try:
        # Check if local Elasticsearch is accessible
        if not local_es.ping():
            print("❌ Cannot connect to local Elasticsearch on port 9201")
            print("💡 Make sure it's running with: ./bin/elasticsearch -Ehttp.port=9201")
            return
        
        print("✅ Connected to local Elasticsearch on port 9201")
        
        # Check if Docker Elasticsearch is accessible
        if not docker_es.ping():
            print("❌ Cannot connect to Docker Elasticsearch on port 9200")
            print("💡 Make sure Docker is running with: docker-compose up -d elasticsearch")
            return
        
        print("✅ Connected to Docker Elasticsearch on port 9200")
        
        if not local_es:
            print("❌ Could not find local Elasticsearch. Is it running?")
            print("💡 Try starting it with: brew services start elasticsearch")
            return
        
        # Get all animal-humane indices from local
        local_indices = local_es.cat.indices(format="json")
        animal_indices = [idx["index"] for idx in local_indices if idx["index"].startswith("animal-humane-")]
        
        print(f"📊 Found {len(animal_indices)} animal-humane indices to migrate:")
        for idx in sorted(animal_indices):
            print(f"   - {idx}")
        
        if not animal_indices:
            print("❌ No animal-humane indices found in local Elasticsearch")
            return
        
        # Migrate each index
        for index_name in animal_indices:
            print(f"\n🔄 Migrating {index_name}...")
            
            # Check if index already exists in Docker
            if docker_es.indices.exists(index=index_name):
                print(f"   ⚠️  Index {index_name} already exists in Docker, skipping")
                continue
            
            # Get index mapping and settings from source
            mapping = local_es.indices.get_mapping(index=index_name)
            settings = local_es.indices.get_settings(index=index_name)
            
            # Create index in Docker with same mapping
            docker_es.indices.create(
                index=index_name,
                body={
                    "mappings": mapping[index_name]["mappings"],
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
            )
            
            # Migrate documents
            docs = []
            doc_count = 0
            
            for doc in scan(local_es, index=index_name, query={"query": {"match_all": {}}}):
                docs.append({
                    "_index": index_name,
                    "_id": doc["_id"],
                    "_source": doc["_source"]
                })
                doc_count += 1
                
                # Bulk insert every 100 documents
                if len(docs) >= 100:
                    bulk(docker_es, docs)
                    docs = []
            
            # Insert remaining documents
            if docs:
                bulk(docker_es, docs)
            
            print(f"   ✅ Migrated {doc_count} documents")
        
        # Update the alias to point to the most recent index
        if animal_indices:
            most_recent = sorted(animal_indices)[-1]
            docker_es.indices.update_aliases(body={
                "actions": [
                    {"remove": {"index": "*", "alias": "animal-humane-latest"}},
                    {"add": {"index": most_recent, "alias": "animal-humane-latest"}},
                ]
            })
            print(f"\n🔗 Updated alias to point to {most_recent}")
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"📊 Migrated {len(animal_indices)} indices")
        print(f"🐳 Docker Elasticsearch now contains all your historical data")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()