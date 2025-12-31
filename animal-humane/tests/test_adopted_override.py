from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
import os, json


def test_adopted_override_applies():
    # Create overrides file
    os.makedirs('overrides', exist_ok=True)
    data = [{"dog_id": 212434888, "name": "Prince Charming"}, {"dog_id": 212428689, "name": "Navy"}]
    with open('overrides/adopted_today.json', 'w', encoding='utf-8') as fh:
        json.dump(data, fh)

    handler = ElasticsearchHandler(host='http://localhost:9200', index_name='animal-humane-latest')
    handler.es = None
    handler.get_all_ids = lambda idx: []
    handler.get_returned_dogs = lambda avail, idx: []
    availables = []

    groups = handler.get_dog_groups(availables, 'animal-humane-20251230-1500')
    adopted_ids = {d['dog_id'] for d in groups['adopted_dogs']}

    assert 212434888 in adopted_ids
    assert 212428689 in adopted_ids

    # cleanup
    os.remove('overrides/adopted_today.json')
