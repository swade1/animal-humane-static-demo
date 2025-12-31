from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

class DummyES:
    def __init__(self, hits):
        self._hits = hits
    def search(self, index, body):
        return {'hits': {'hits': self._hits}, 'hits_total': len(self._hits)}


def test_recent_adopted_missing_with_trial_history_promotes_to_adopted():
    handler = ElasticsearchHandler(host='http://localhost:9200', index_name='animal-humane-latest')
    trial_dog = {'name': 'Prince Charming', 'dog_id': 212434888, 'url': 'https://new.shelterluv.com/embed/animal/212434888', 'location': 'Trial Adoption'}
    # Simulate dog is MISSING from today's availables (i.e., disappeared during today's scrape)
    availables = []

    # Mock ES recent adopted hit (within 8-day window) and a trial-adoption hit in the past
    recent_adopted_hit = {'_source': {'name': 'Prince Charming', 'id': 212434888, 'status': 'adopted', 'timestamp': '2025-12-23T11:01:11', 'location': ''}}
    trial_history_hit = {'_source': {'name': 'Prince Charming', 'id': 212434888, 'status': 'available', 'timestamp': '2025-12-23T08:46:16', 'location': 'Main Campus- Trial Adoption'}}

    # DummyES will return both hits for any search; the handler logic will use them appropriately
    handler.es = DummyES([recent_adopted_hit, trial_history_hit])
    handler.get_all_ids = lambda idx: []
    handler.get_returned_dogs = lambda avail, idx: []

    groups = handler.get_dog_groups(availables, 'animal-humane-20251230-1500')

    adopted_ids = {d['dog_id'] for d in groups['adopted_dogs']}
    trial_ids = {d['dog_id'] for d in groups['trial_adoption_dogs']}

    assert 212434888 in adopted_ids
    assert 212434888 not in trial_ids
