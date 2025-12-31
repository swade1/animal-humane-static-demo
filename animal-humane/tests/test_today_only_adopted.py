from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

class DummyES:
    def __init__(self, hits):
        self._hits = hits
    def search(self, index, body):
        return {'hits': {'hits': self._hits}}


def test_today_adopted_includes_only_today_timestamp():
    handler = ElasticsearchHandler(host='http://localhost:9200', index_name='animal-humane-latest')
    # Simulate today's index returning two adopted hits, one today and one earlier
    hit_today = {'_source': {'name': 'Prince Charming', 'id': 212434888, 'status': 'adopted', 'timestamp': '2025-12-30T12:00:00', 'location': ''}}
    hit_yesterday = {'_source': {'name': 'Old Dog', 'id': 999999999, 'status': 'adopted', 'timestamp': '2025-12-29T12:00:00', 'location': ''}}

    handler.es = DummyES([hit_today, hit_yesterday])
    handler.get_all_ids = lambda idx: []
    availables = []  # none available

    groups = handler.get_dog_groups(availables, 'animal-humane-20251230-1500')

    adopted_ids = {d['dog_id'] for d in groups['adopted_dogs']}

    assert 212434888 in adopted_ids
    assert 999999999 not in adopted_ids
