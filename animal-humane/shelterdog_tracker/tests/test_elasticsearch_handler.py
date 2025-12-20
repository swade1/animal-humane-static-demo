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
        # Test data setup
        index_name = "test-index"
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

        # Test with no status filter (should return all)
        distribution = self.handler.get_length_of_stay_distribution()
        # We're getting all the intervals, so just check that we have data
        self.assertTrue(len(distribution) > 0)

        # Test with 'adopted' status filter
        adopted_distribution = self.handler.get_length_of_stay_distribution("adopted")
        self.assertTrue(len(adopted_distribution) > 0)
        # Check that we have the expected values
        adopted_values = {d["range_start"] for d in adopted_distribution}
        self.assertTrue(5 in adopted_values)
        self.assertTrue(15 in adopted_values)

if __name__ == "__main__":
    unittest.main()
