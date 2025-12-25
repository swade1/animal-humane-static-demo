#!/usr/bin/env python3
"""
Script to identify dogs in location_info.jsonl whose IDs don't exist in Elasticsearch
"""
import json
import sys
import os
from typing import Set, Dict, List

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

def load_dog_data_from_file(file_path: str) -> Dict[int, str]:
    """Load all dog data from the location_info.jsonl file"""
    dog_data = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    dog_info = json.loads(line)
                    dog_id = dog_info.get('id')
                    dog_name = dog_info.get('name', 'Unknown')
                    if dog_id is not None:
                        dog_data[int(dog_id)] = dog_name
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid dog data on line {line_num}: {e}")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    return dog_data

def get_existing_dog_ids_from_elasticsearch() -> Set[int]:
    """Get all dog IDs that exist in Elasticsearch"""
    try:
        # Get Elasticsearch host from environment variable for Docker
        es_host = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')

        # Initialize Elasticsearch handler
        handler = ElasticsearchHandler(
            host=es_host,
            index_name="animal-humane-latest"
        )

        # Get all existing dog IDs from Elasticsearch
        # We'll query across all animal-humane indices
        existing_ids = set()

        # Get only open indices to avoid closed index exceptions
        indices_info = handler.es.cat.indices(format='json')
        open_indices = [index['index'] for index in indices_info
                       if index.get('status') == 'open' and index['index'].startswith('animal-humane-')]

        if not open_indices:
            print("No open animal-humane indices found in Elasticsearch")
            return set()

        print(f"Querying {len(open_indices)} open indices...")

        # To avoid HTTP line length limits, we'll query indices in batches
        batch_size = 50  # Process 50 indices at a time
        all_batches = [open_indices[i:i + batch_size] for i in range(0, len(open_indices), batch_size)]

        for batch_num, batch_indices in enumerate(all_batches, 1):
            print(f"Processing batch {batch_num}/{len(all_batches)} ({len(batch_indices)} indices)...")

            # Query for all unique IDs in this batch
            query = {
                "size": 0,
                "aggs": {
                    "unique_ids": {
                        "terms": {
                            "field": "id",
                            "size": 100000  # Large size to get all IDs
                        }
                    }
                },
                "query": {"match_all": {}}
            }

            try:
                response = handler.es.search(index=batch_indices, body=query)

                # Extract IDs from aggregation results
                if "aggregations" in response and "unique_ids" in response["aggregations"]:
                    for bucket in response["aggregations"]["unique_ids"]["buckets"]:
                        existing_ids.add(int(bucket["key"]))
            except Exception as e:
                print(f"Warning: Failed to query batch {batch_num}: {e}")
                continue

        return existing_ids

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        sys.exit(1)

def main():
    """Main function"""
    # Path to the location_info.jsonl file
    file_path = os.path.join(os.path.dirname(__file__), 'location_info.jsonl')

    print("Loading dog data from location_info.jsonl...")
    file_dog_data = load_dog_data_from_file(file_path)
    print(f"Found {len(file_dog_data)} dogs in the file")

    print("\nQuerying Elasticsearch for existing dog IDs...")
    es_dog_ids = get_existing_dog_ids_from_elasticsearch()
    print(f"Found {len(es_dog_ids)} dog IDs in Elasticsearch")

    # Find dogs that exist in the file but not in Elasticsearch
    file_dog_ids = set(file_dog_data.keys())
    missing_ids = file_dog_ids - es_dog_ids

    print(f"\nFound {len(missing_ids)} dogs that exist in the file but not in Elasticsearch")

    if missing_ids:
        print("\nMissing dogs (ID: Name):")
        for dog_id in sorted(missing_ids):
            dog_name = file_dog_data[dog_id]
            print(f"  {dog_id}: {dog_name}")

        # Optionally, save to a file
        output_file = os.path.join(os.path.dirname(__file__), 'missing_dogs.txt')
        with open(output_file, 'w') as f:
            f.write("Missing dogs (ID: Name):\n")
            for dog_id in sorted(missing_ids):
                dog_name = file_dog_data[dog_id]
                f.write(f"{dog_id}: {dog_name}\n")

        print(f"\nSaved missing dogs to: {output_file}")
    else:
        print("\nAll dogs from the file exist in Elasticsearch!")

if __name__ == "__main__":
    main()