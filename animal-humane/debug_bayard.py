#!/usr/bin/env python3
"""
Debug script to check Bayard Animal Control dog count
"""
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

def main():
    print("🔍 Debugging Bayard Animal Control dog count")
    print("=" * 50)
    
    handler = ElasticsearchHandler(host="http://localhost:9200", index_name="animal-humane-latest")
    
    # Query for all dogs from Bayard Animal Control and Clayton
    origins_to_check = ["Bayard Animal Control", "Clayton"]
    
    for origin_name in origins_to_check:
        print(f"\n1. Searching for all {origin_name} dogs...")
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"origin.keyword": origin_name}}
                    ],
                    "must_not": [
                        {"term": {"status.keyword": "adopted"}}
                    ]
                }
            },
            "_source": ["id", "name", "origin", "status", "latitude", "longitude"],
            "size": 100
        }
        response = handler.es.search(index="animal-humane-*", body=query)
        
        dogs = []
        unique_ids = set()
        
        for hit in response['hits']['hits']:
            source = hit['_source']
            dog_id = source.get('id')
            name = source.get('name')
            status = source.get('status')
            lat = source.get('latitude')
            lon = source.get('longitude')
            
            dogs.append({
                'id': dog_id,
                'name': name,
                'status': status,
                'latitude': lat,
                'longitude': lon,
                'index': hit['_index']
            })
            
            if dog_id:
                unique_ids.add(dog_id)
        
        print(f"📊 Total documents found for {origin_name}: {len(dogs)}")
        print(f"🐕 Unique dog IDs for {origin_name}: {len(unique_ids)}")
        print(f"🆔 Unique IDs: {sorted(unique_ids)}")
        
        print(f"\n📋 All {origin_name} dogs found:")
        for dog in dogs:
            print(f"  - {dog['name']} (ID: {dog['id']}) - Status: {dog['status']} - Coords: ({dog['latitude']}, {dog['longitude']}) - Index: {dog['index']}")
        
        # Check for duplicate IDs
        id_counts = {}
        for dog in dogs:
            dog_id = dog['id']
            if dog_id in id_counts:
                id_counts[dog_id].append(dog)
            else:
                id_counts[dog_id] = [dog]
        
        print(f"\n🔍 Checking for duplicate IDs in {origin_name}:")
        for dog_id, dog_list in id_counts.items():
            if len(dog_list) > 1:
                print(f"  ⚠️  ID {dog_id} appears {len(dog_list)} times:")
                for dog in dog_list:
                    print(f"     - {dog['name']} in {dog['index']}")
            else:
                print(f"  ✅ ID {dog_id} ({dog_list[0]['name']}) appears once")
    
    # Test the new get_origins method
    print("\n🧪 Testing get_origins() method:")
    origins = handler.get_origins()
    
    print("All origins with counts:")
    for origin in origins:
        origin_name = origin.get('origin', '')
        if "Bayard" in origin_name or "Clayton" in origin_name:
            print(f"  📍 {origin_name}: {origin['count']} dogs (lat: {origin.get('latitude')}, lon: {origin.get('longitude')})")
    
    # Check if Bayard and Clayton are in the results
    bayard_found = any("Bayard" in origin.get('origin', '') for origin in origins)
    clayton_found = any("Clayton" in origin.get('origin', '') for origin in origins)
    
    print(f"\n✅ Bayard Animal Control in results: {bayard_found}")
    print(f"✅ Clayton in results: {clayton_found}")

if __name__ == "__main__":
    main()