#!/usr/bin/env python3
"""
Test script to update Phelps' metadata in Elasticsearch with location_info.jsonl data
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

def test_phelps_update():
    """Test updating Phelps' bite_quarantine from 0 to 2"""

    # Initialize Elasticsearch handler
    es_handler = ElasticsearchHandler(host="http://localhost:9200", index_name="animal-humane-*")

    # Phelps' dog ID - we need to find this
    # First, let's search for Phelps to get his ID
    phelps_docs = es_handler.get_dog_by_name("Phelps")

    if not phelps_docs:
        print("Phelps not found in Elasticsearch")
        return

    # Get Phelps' ID from the first document
    phelps_id = phelps_docs[0]['id']
    print(f"Found Phelps with ID: {phelps_id}")
    print(f"Current bite_quarantine: {phelps_docs[0].get('bite_quarantine', 0)}")

    # Update Phelps' metadata
    print("Updating Phelps' metadata...")
    es_handler.update_metadata_from_location_info(dog_ids=[phelps_id])

    # Verify the update
    print("Verifying update...")
    updated_docs = es_handler.get_dog_by_name("Phelps")
    if updated_docs:
        print(f"Updated bite_quarantine: {updated_docs[0].get('bite_quarantine', 0)} (type: {type(updated_docs[0].get('bite_quarantine', 0))})")
        print(f"Updated returned: {updated_docs[0].get('returned', 0)} (type: {type(updated_docs[0].get('returned', 0))})")
        print(f"Updated origin: {updated_docs[0].get('origin', 'Unknown')}")

        # Also check what location_info.jsonl says
        import json
        with open('location_info.jsonl', 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data['id'] == phelps_id:
                        print(f"location_info.jsonl bite_quarantine: {data.get('bite_quarantine', 0)} (type: {type(data.get('bite_quarantine', 0))})")
                        print(f"location_info.jsonl returned: {data.get('returned', 0)} (type: {type(data.get('returned', 0))})")
                        print(f"location_info.jsonl origin: {data.get('origin', 'Unknown')}")
                        break
                except json.JSONDecodeError:
                    continue

if __name__ == "__main__":
    test_phelps_update()