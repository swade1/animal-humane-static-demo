import unittest
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

class TestElasticsearchHandler(unittest.TestCase):

    def setUp(self):
        # Create a mock Elasticsearch client
        self.es = Elasticsearch(
            "http://localhost:9200",
            request_timeout=60,
            verify_certs=False,
            ssl_show_warn=False
        )
        self.handler = ElasticsearchHandler("http://localhost:9200", "test-index")

    def test_get_length_of_stay_distribution(self):
        # Use a unique index name to avoid conflicts
        import time
        index_name = f"test-index-{int(time.time())}"
        
        # Delete index if it exists
        self.handler.es.indices.delete(index=index_name, ignore=[400, 404])
        
        self.handler.es.indices.create(index=index_name, ignore=400)

        # Create test documents with length_of_stay_days
        docs = [
            {
                "_index": index_name,
                "_source": {
                    "id": 1,
                    "status": "adopted",
                    "length_of_stay_days": 5
                }
            },
            {
                "_index": index_name,
                "_source": {
                    "id": 2,
                    "status": "available",
                    "length_of_stay_days": 10
                }
            },
            {
                "_index": index_name,
                "_source": {
                    "id": 3,
                    "status": "adopted",
                    "length_of_stay_days": 15
                }
            },
            {
                "_index": index_name,
                "_source": {
                    "id": 4,
                    "status": "available",
                    "length_of_stay_days": 20
                }
            }
        ]

        # Index the test documents
        for doc in docs:
            self.handler.es.index(index=doc["_index"], body=doc["_source"])
        
        # Refresh the index to make documents searchable
        self.handler.es.indices.refresh(index=index_name)

        # Test with no status filter (should return available dogs by default)
        distribution = self.handler.get_length_of_stay_distribution(index_pattern=index_name)
        # Check that we have the expected structure
        self.assertIn("bins", distribution)
        self.assertIn("metadata", distribution)
        self.assertTrue(len(distribution["bins"]) > 0)

        # Test with 'adopted' status filter
        adopted_distribution = self.handler.get_length_of_stay_distribution("adopted", index_pattern=index_name)
        self.assertIn("bins", adopted_distribution)
        self.assertIn("metadata", adopted_distribution)
        self.assertIsInstance(adopted_distribution["bins"], list)
        self.assertIsInstance(adopted_distribution["metadata"], dict)

        # Check that adopted dogs are found (should be 2 dogs with status "adopted")
        adopted_dogs = []
        for bin_data in adopted_distribution["bins"]:
            adopted_dogs.extend(bin_data["dogs"])

        # Should find the 2 adopted dogs
        self.assertEqual(len(adopted_dogs), 2, f"Expected 2 adopted dogs, found {len(adopted_dogs)}")
        
        # Check that the dogs have the expected length_of_stay_days values
        los_values = sorted([dog["length_of_stay_days"] for dog in adopted_dogs])
        self.assertEqual(los_values, [5, 15], f"Expected [5, 15], found {los_values}")

if __name__ == "__main__":
    unittest.main()
