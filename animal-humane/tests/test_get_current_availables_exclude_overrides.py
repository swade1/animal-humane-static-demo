from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
import os, json


def test_get_current_availables_excludes_overrides(tmp_path, monkeypatch):
    # Setup overrides file
    overrides_dir = tmp_path / "overrides"
    overrides_dir.mkdir()
    overrides_file = overrides_dir / "adopted_today.json"
    overrides_file.write_text('[{"dog_id": 212428689, "name": "Navy"}]')

    # Monkeypatch cwd to tmp_path so handler reads overrides from there
    monkeypatch.chdir(tmp_path)

    handler = ElasticsearchHandler(host='http://localhost:9200', index_name='animal-humane-latest')

    # Build a fake result from ES search: two dogs, Navy and SomeoneElse
    # We'll stub the search method to return hits sorted by most recent index
    class DummyES:
        def search(self, index, body):
            return {
                'hits': {'hits': [
                    {'_source': {'id': 212428689, 'name': 'Navy', 'status': 'Available', 'location': 'Main Campus- Big Blue, BB-12', 'url': 'https://new.shelterluv.com/embed/animal/212428689'}},
                    {'_source': {'id': 212111111, 'name': 'SomeoneElse', 'status': 'Available', 'location': 'Main Campus- MKS-1', 'url': 'https://new.shelterluv.com/embed/animal/212111111'}}
                ]}
            }

    handler.es = DummyES()

    # Call get_current_availables which should read overrides and exclude Navy
    avail = handler.get_current_availables()
    ids = {d['dog_id'] for d in avail}

    assert 212428689 not in ids
    assert 212111111 in ids
