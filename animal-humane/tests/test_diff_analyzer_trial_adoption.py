import pytest
from scheduler.diff_analyzer import DiffAnalyzer


class DummyAnalyzer(DiffAnalyzer):
    def __init__(self, index_map):
        super().__init__()
        self._index_map = index_map

    def get_dogs_from_index(self, index_name):
        return self._index_map.get(index_name, {})


def test_trial_adoption_formalized_counts_as_adopted():
    # Setup indices: current (no Prince), previous (no Prince), historical recent index where
    # Prince's record was updated to 'adopted'
    prince_id = '212434888'
    current_index = 'animal-humane-20251230-1500'
    previous_index = 'animal-humane-20251229-1500'
    recent_historical_index = 'animal-humane-20251229-0900'
    old_trial_index = 'animal-humane-20251223-1100'

    # Define index contents
    index_map = {
        current_index: {},
        previous_index: {},
        recent_historical_index: {
            prince_id: {'name': 'Prince Charming', 'status': 'adopted', 'location': ''}
        },
        old_trial_index: {
            prince_id: {'name': 'Prince Charming', 'status': 'trial', 'location': 'Trial Adoption'}
        }
    }

    analyzer = DummyAnalyzer(index_map)

    results = analyzer.analyze_recent_changes(current_index, previous_index, [recent_historical_index, old_trial_index])

    adopted_ids = {d['id'] for d in results.get('adopted_dogs', [])}
    assert prince_id in adopted_ids, "Prince Charming (trial->adopted) should appear in adopted_dogs"


def test_old_adopted_record_is_not_considered_recent():
    prince_id = '212434888'
    current_index = 'animal-humane-20251230-1500'
    previous_index = 'animal-humane-20251229-1500'
    stale_adopted_index = 'animal-humane-20251220-0900'  # 10 days before current_index
    old_trial_index = 'animal-humane-20251223-1100'

    index_map = {
        current_index: {},
        previous_index: {},
        stale_adopted_index: {
            prince_id: {'name': 'Prince Charming', 'status': 'adopted', 'location': ''}
        },
        old_trial_index: {
            prince_id: {'name': 'Prince Charming', 'status': 'trial', 'location': 'Trial Adoption'}
        }
    }

    analyzer = DummyAnalyzer(index_map)
    results = analyzer.analyze_recent_changes(current_index, previous_index, [stale_adopted_index, old_trial_index])

    adopted_ids = {d['id'] for d in results.get('adopted_dogs', [])}
    assert prince_id not in adopted_ids, "Prince Charming with stale adopted record should NOT appear in adopted_dogs"