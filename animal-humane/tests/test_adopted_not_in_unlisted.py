from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
import os, json


def test_override_adopted_not_in_other_unlisted():
    # Write override file
    os.makedirs('overrides', exist_ok=True)
    data = [{"dog_id": 212428689, "name": "Navy"}]
    with open('overrides/adopted_today.json', 'w', encoding='utf-8') as fh:
        json.dump(data, fh)

    handler = ElasticsearchHandler(host='http://localhost:9200', index_name='animal-humane-latest')

    # Simulate Navy being in today's availables but not in index (unlisted)
    navy = {'name': 'Navy', 'dog_id': 212428689, 'url': 'https://new.shelterluv.com/embed/animal/212428689', 'location': 'Main Campus- Big Blue, BB-12'}
    availables = [navy]

    # Stub index ids to simulate missing from index
    handler.get_all_ids = lambda idx: []
    handler.get_returned_dogs = lambda avail, idx: []

    groups = handler.get_dog_groups(availables, 'animal-humane-20251230-1500')

    adopted_ids = {d['dog_id'] for d in groups['adopted_dogs']}
    other_ids = {d['dog_id'] for d in groups['other_unlisted_dogs']}
    trial_ids = {d['dog_id'] for d in groups['trial_adoption_dogs']}

    assert 212428689 in adopted_ids
    assert 212428689 not in other_ids
    assert 212428689 not in trial_ids

    # cleanup
    os.remove('overrides/adopted_today.json')