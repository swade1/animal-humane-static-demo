#!/usr/bin/env python3
"""
Update static data files for the portfolio demo deployment
This includes both timestamp updates and location_info.jsonl synchronization
"""
import json
import requests
from datetime import datetime
import os
import shutil
from pathlib import Path

def get_latest_index_timestamp():
    """Get the timestamp from the most recent Elasticsearch index"""
    try:
        # Query Elasticsearch for indices
        response = requests.get('http://localhost:9200/_cat/indices/animal-humane-*?format=json&h=index')
        if response.status_code != 200:
            print(f"❌ Failed to query Elasticsearch: {response.status_code}")
            return None
            
        indices = response.json()
        if not indices:
            print("❌ No animal-humane indices found")
            return None
            
        # Find the most recent index
        index_names = [idx['index'] for idx in indices]
        latest_index = sorted(index_names)[-1]
        print(f"📊 Latest index: {latest_index}")
        
        # Parse timestamp from index name (format: animal-humane-YYYYMMDD-HHMM)
        if '-' not in latest_index:
            print(f"❌ Invalid index name format: {latest_index}")
            return None
            
        parts = latest_index.split('-')
        if len(parts) < 4:
            print(f"❌ Invalid index name format: {latest_index}")
            return None
            
        date_part = parts[2]  # YYYYMMDD
        time_part = parts[3]  # HHMM
        
        # Convert to datetime
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        
        dt = datetime(year, month, day, hour, minute)
        
        return dt, latest_index
        
    except Exception as e:
        print(f"❌ Error querying Elasticsearch: {e}")
        return None

def update_timestamp_file(dt, source_index):
    """Update the last-updated.json file with the given timestamp"""
    timestamp_data = {
        "lastUpdated": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "human_readable": dt.strftime("%B %d, %Y at %I:%M %p UTC"),
        "timestamp": int(dt.timestamp()),
        "source_index": source_index
    }
    
    # Write to the React app's public directory
    output_file = Path("react-app/public/api/last-updated.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(timestamp_data, f, indent=2)
    
    print(f"✅ Updated timestamp file:")
    print(f"   📅 Date: {timestamp_data['human_readable']}")
    print(f"   🔍 Source: {source_index}")

def sync_location_info():
    """Copy location_info.jsonl to React public directory"""
    source = Path("location_info.jsonl")
    target = Path("react-app/public/location_info.jsonl")
    
    if not source.exists():
        print(f"❌ Source file not found: {source}")
        return False
    
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"✅ Synced location_info.jsonl to React public directory")
        
        # Count entries for verification
        with open(source, 'r') as f:
            lines = sum(1 for line in f if line.strip())
        print(f"   📊 {lines} dog records synchronized")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing location_info.jsonl: {e}")
        return False

def main():
    """Main function to update all static data - DISABLED for manual timestamp control"""
    print("🔄 Static data update DISABLED - manual timestamp control active...")
    print("⚠️  Skipping all updates to preserve manual timestamp settings")
    print("🎉 Static data update complete (no changes made)!")

if __name__ == "__main__":
    main()