#!/usr/bin/env python3
"""
Update the timestamp file based on the most recent Elasticsearch index
"""
import json
import requests
from datetime import datetime
import os

def get_latest_index_timestamp():
    """Get the timestamp from the most recent animal-humane index"""
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
        
        # Create timestamp data
        iso_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        human_date = dt.strftime("%B %d, %Y at %I:%M %p UTC")
        unix_timestamp = int(dt.timestamp())
        
        return {
            'lastUpdated': iso_date,
            'human_readable': human_date,
            'timestamp': unix_timestamp,
            'source_index': latest_index
        }
        
    except Exception as e:
        print(f"❌ Error getting latest index: {e}")
        return None

def update_timestamp_file():
    """Update the last-updated.json file with the latest index timestamp"""
    timestamp_data = get_latest_index_timestamp()
    if not timestamp_data:
        return False
        
    # Ensure directory exists
    os.makedirs('react-app/public/api', exist_ok=True)
    
    # Write timestamp file
    with open('react-app/public/api/last-updated.json', 'w') as f:
        json.dump(timestamp_data, f, indent=2)
    
    print(f"✅ Updated timestamp file:")
    print(f"   📅 Date: {timestamp_data['human_readable']}")
    print(f"   🔍 Source: {timestamp_data['source_index']}")
    return True

if __name__ == "__main__":
    print("🔄 Updating timestamp from latest Elasticsearch index...")
    if update_timestamp_file():
        print("🎉 Timestamp updated successfully!")
    else:
        print("❌ Failed to update timestamp")