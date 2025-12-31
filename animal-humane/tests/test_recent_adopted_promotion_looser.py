from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

class DummyES:
    def __init__(self, hits):
        self._hits = hits
    def search(self, index, body):
        return {'hits': {'hits': self._hits}, 'hits_total': len(self._hits)}


def test_recent_adopted_missing_promotes_to_adopted_without_trial_history():
    handler = ElasticsearchHandler(host='http://localhost:9200', index_name='animal-humane-latest')
    # Simulate dog missing from today's availables
    availables = []

    # Mock ES recent adopted hit (within 8-day window) but no trial history hit
    recent_adopted_hit = {'_source': {'name': 'Prince Charming', 'id': 212434888, 'status': 'adopted', 'timestamp': '2025-12-23T11:01:11', 'location': ''}}

    handler.es = DummyES([recent_adopted_hit])
    handler.get_all_ids = lambda idx: []
    handler.get_returned_dogs = lambda avail, idx: []

    groups = handler.get_dog_groups(availables, 'animal-humane-20251230-1500')

    adopted_ids = {d['dog_id'] for d in groups['adopted_dogs']}
    assert 212434888 in adopted_ids
