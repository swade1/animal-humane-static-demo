import pytest
import requests
from fastapi.testclient import TestClient

from api.main import app


def es_available():
    try:
        r = requests.get('http://localhost:9200', timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not es_available(), reason="Elasticsearch not available")
def test_prince_appears_in_public_diff():
    """Integration test: ensure Prince (212434888) appears in adopted_dogs when ES is reachable"""
    # This integration test hits the running API (assumes it's available at localhost:8000)

    # Clear cache to force fresh computation
    resp = requests.post('http://127.0.0.1:8000/api/cache/clear')
    assert resp.status_code == 200

    r = requests.get('http://127.0.0.1:8000/api/diff-analysis')
    assert r.status_code == 200
    data = r.json().get('data', {})
    adopted = data.get('adopted_dogs', [])
    adopted_ids = {d.get('dog_id') for d in adopted}

    assert 212434888 in adopted_ids
