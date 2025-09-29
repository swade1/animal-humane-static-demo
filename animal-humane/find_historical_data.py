#!/usr/bin/env python3
"""
Script to help find your historical Elasticsearch data
"""
import os
import json
import glob
from pathlib import Path

def main():
    print("🔍 Searching for Historical Animal Humane Data")
    print("=" * 50)
    
    # Search for potential data locations
    search_paths = [
        "/usr/local/var/lib/elasticsearch",
        "/usr/local/var/elasticsearch", 
        "/opt/homebrew/var/lib/elasticsearch",
        "/opt/homebrew/var/elasticsearch",
        "~/Library/Application Support/elasticsearch",
        "./elasticsearch_data",
        "./data",
        "."
    ]
    
    found_data = []
    
    print("🔍 Searching common Elasticsearch data directories...")
    for path in search_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            print(f"   Checking: {expanded_path}")
            
            # Look for nodes directory (Elasticsearch data structure)
            nodes_path = os.path.join(expanded_path, "nodes")
            if os.path.exists(nodes_path):
                found_data.append(f"Elasticsearch data directory: {expanded_path}")
            
            # Look for indices directory
            indices_path = os.path.join(expanded_path, "indices")
            if os.path.exists(indices_path):
                found_data.append(f"Indices directory: {expanded_path}")
    
    print("\n🔍 Searching for JSON export files...")
    json_patterns = [
        "*animal-humane*.json",
        "*backup*.json", 
        "*export*.json",
        "*.json"
    ]
    
    for pattern in json_patterns:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            if os.path.getsize(file) > 1000:  # Only show files > 1KB
                found_data.append(f"JSON file: {file} ({os.path.getsize(file)} bytes)")
    
    print("\n🔍 Searching for snapshot directories...")
    snapshot_patterns = [
        "*snapshot*",
        "*backup*",
        "snapshots",
        "backups"
    ]
    
    for pattern in snapshot_patterns:
        dirs = glob.glob(pattern, recursive=True)
        for dir_path in dirs:
            if os.path.isdir(dir_path):
                files_in_dir = os.listdir(dir_path)
                if files_in_dir:
                    found_data.append(f"Snapshot directory: {dir_path} (contains {len(files_in_dir)} files)")
    
    print("\n📊 Results:")
    print("=" * 20)
    
    if found_data:
        for item in found_data:
            print(f"✅ {item}")
        
        print(f"\n💡 Found {len(found_data)} potential data locations!")
        print("\nNext steps:")
        print("1. Check the Elasticsearch data directories for your indices")
        print("2. Look for JSON files that might contain your exported data")
        print("3. Check snapshot directories for Elasticsearch snapshots")
        
    else:
        print("❌ No obvious data locations found")
        print("\n💡 Your data might be:")
        print("1. In a different Elasticsearch installation")
        print("2. In a custom data directory")
        print("3. In cloud storage or external backup")
        print("4. Lost during the Docker setup process")
    
    print(f"\n🔧 To check what's currently running:")
    print("   lsof -i :9200")
    print("   brew services list | grep elasticsearch")

if __name__ == "__main__":
    main()