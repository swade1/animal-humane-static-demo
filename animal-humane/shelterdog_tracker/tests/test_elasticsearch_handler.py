#These tests presuppose that an index named 'dogs' exists
#Usage (run from shelterdog_project directory) to execute a single function
#python3 -m unittest -v shelterdog_tracker.tests.test_elasticsearch_handler.TestElasticsearchHandler.test_push_dog_to_elasticsearch

import unittest
from unittest.mock import MagicMock
from datetime import datetime
from shelterdog_tracker.dog import Dog
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

class TestElasticsearchHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up ElasticsearchHandler instance once for all tests
        cls.handler = ElasticsearchHandler(
            host="http://localhost:9200",
            index_name="dogs"
        )
        # Optionally, ingest test data here if not already present

    def test_get_dog_by_id(self):
        # Replace with a known dog ID ingested in your test index
        test_id = 208812460 
        dog = self.handler.get_dog_by_id(test_id)
        print(f"dog inside test is: {dog}")
        print()
        self.assertIsNotNone(dog, f"Dog with id {test_id} should be found.")
        # Optionally, check specific fields
        self.assertEqual(dog.get('id'), test_id)

    def test_get_dog_by_name(self):
        test_name = "Nova"
        dog = self.handler.get_dog_by_name(test_name)
        print(f"dog inside test is: {test_name}")
        self.assertIsNotNone(dog, f"Dog with name {test_name} should be found.")
        self.assertIsInstance(dogs, list)
        self.assertTrue(any(dog.get('name') == test_name for dog in dogs),
                        f"At least one dog named {test_name} should be found.")
    def test_push_dog_to_elasticsearch(self):
        test_dog = Dog(dog_id=1, name="Fido", intake_date=datetime(2025, 7, 16))
        handler = ElasticsearchHandler(host="http://localhost:9200", index_name="dogs")
        handler.es = MagicMock()
        handler.es.index.return_value = {
            "_index": "dogs",
            "_id": "1",
            "result": "created"
        }
        response = handler.push_dog_to_elasticsearch(test_dog, "dogs")
        self.assertEqual(response["result"], "created")

    # Add more tests as needed, e.g., for non-existent IDs or names

if __name__ == '__main__':
    unittest.main()

