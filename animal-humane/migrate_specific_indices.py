#!/usr/bin/env python3
"""
Migrate specific Elasticsearch indices to Docker container
Usage: python migrate_specific_indices.py [options]
"""
import json
import requests
import argparse
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, bulk

def get_available_indices(es_client, pattern="animal-humane-"):
    """Get list of available indices matching pattern"""
    try:
        indices = es_client.cat.indices(format="json")
        matching_indices = [idx["index"] for idx in indices if idx["index"].startswith(pattern)]
        return sorted(matching_indices)
    except Exception as e:
        print(f"❌ Error getting indices: {e}")
        return []

def migrate_index(local_es, docker_es, index_name, force=False):
    """Migrate a single index from local to Docker"""
    print(f"\n🔄 Migrating {index_name}...")
    
    # Check if index already exists in Docker
    if docker_es.indices.exists(index=index_name):
        if not force:
            print(f"   ⚠️  Index {index_name} already exists in Docker, skipping")
            print(f"   💡 Use --force to overwrite existing index")
            return False
        else:
            print(f"   🔄 Index {index_name} exists, overwriting...")
            docker_es.indices.delete(index=index_name)
    
    try:
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
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to migrate {index_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Migrate specific Elasticsearch indices to Docker")
    parser.add_argument("--indices", "-i", nargs="+", help="Specific indices to migrate (space-separated)")
    parser.add_argument("--pattern", "-p", default="animal-humane-", help="Pattern to match indices (default: animal-humane-)")
    parser.add_argument("--local-port", default=9201, type=int, help="Local Elasticsearch port (default: 9201)")
    parser.add_argument("--docker-port", default=9200, type=int, help="Docker Elasticsearch port (default: 9200)")
    parser.add_argument("--force", "-f", action="store_true", help="Force overwrite existing indices")
    parser.add_argument("--list", "-l", action="store_true", help="List available indices and exit")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode to select indices")
    
    args = parser.parse_args()
    
    print("🔄 Migrating Elasticsearch Data to Docker")
    print("=" * 45)
    
    # Source: Your local Elasticsearch
    local_host = f"http://localhost:{args.local_port}"
    print(f"🔍 Connecting to local Elasticsearch on port {args.local_port}...")
    local_es = Elasticsearch(local_host)
    
    # Target: Docker Elasticsearch
    docker_host = f"http://localhost:{args.docker_port}"
    print(f"🔍 Connecting to Docker Elasticsearch on port {args.docker_port}...")
    docker_es = Elasticsearch(docker_host)
    
    try:
        # Check connections
        if not local_es.ping():
            print(f"❌ Cannot connect to local Elasticsearch on port {args.local_port}")
            print("💡 Make sure it's running")
            return
        
        print(f"✅ Connected to local Elasticsearch on port {args.local_port}")
        
        if not docker_es.ping():
            print(f"❌ Cannot connect to Docker Elasticsearch on port {args.docker_port}")
            print("💡 Make sure Docker is running with: docker-compose up -d elasticsearch")
            return
        
        print(f"✅ Connected to Docker Elasticsearch on port {args.docker_port}")
        
        # Get available indices
        available_indices = get_available_indices(local_es, args.pattern)
        
        if not available_indices:
            print(f"❌ No indices found matching pattern '{args.pattern}'")
            return
        
        print(f"\n📊 Found {len(available_indices)} indices matching pattern '{args.pattern}':")
        for i, idx in enumerate(available_indices, 1):
            print(f"   {i:2d}. {idx}")
        
        # Handle different modes
        if args.list:
            print("\n✅ Listed available indices")
            return
        
        indices_to_migrate = []
        
        if args.interactive:
            print(f"\n🔍 Interactive mode - Select indices to migrate:")
            print("Enter index numbers (space-separated) or 'all' for all indices:")
            choice = input("> ").strip()
            
            if choice.lower() == 'all':
                indices_to_migrate = available_indices
            else:
                try:
                    selected_numbers = [int(x) for x in choice.split()]
                    indices_to_migrate = [available_indices[i-1] for i in selected_numbers if 1 <= i <= len(available_indices)]
                except ValueError:
                    print("❌ Invalid selection")
                    return
                    
        elif args.indices:
            # Validate specified indices
            for idx in args.indices:
                if idx in available_indices:
                    indices_to_migrate.append(idx)
                else:
                    print(f"⚠️  Warning: Index '{idx}' not found in available indices")
            
            if not indices_to_migrate:
                print("❌ No valid indices specified")
                return
        else:
            # Default: migrate all matching indices
            indices_to_migrate = available_indices
        
        print(f"\n🎯 Will migrate {len(indices_to_migrate)} indices:")
        for idx in indices_to_migrate:
            print(f"   - {idx}")
        
        # Confirm migration
        if not args.force:
            confirm = input(f"\n❓ Proceed with migration? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Migration cancelled")
                return
        
        # Migrate indices
        successful_migrations = 0
        for index_name in indices_to_migrate:
            if migrate_index(local_es, docker_es, index_name, args.force):
                successful_migrations += 1
        
        # Update alias if we have animal-humane indices
        animal_indices = [idx for idx in indices_to_migrate if idx.startswith("animal-humane-")]
        if animal_indices:
            most_recent = sorted(animal_indices)[-1]
            try:
                docker_es.indices.update_aliases(body={
                    "actions": [
                        {"remove": {"index": "*", "alias": "animal-humane-latest"}},
                        {"add": {"index": most_recent, "alias": "animal-humane-latest"}},
                    ]
                })
                print(f"\n🔗 Updated alias to point to {most_recent}")
            except Exception as e:
                print(f"⚠️  Warning: Could not update alias: {e}")
        
        print(f"\n🎉 Migration completed!")
        print(f"📊 Successfully migrated {successful_migrations}/{len(indices_to_migrate)} indices")
        print(f"🐳 Docker Elasticsearch now contains the selected data")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()







