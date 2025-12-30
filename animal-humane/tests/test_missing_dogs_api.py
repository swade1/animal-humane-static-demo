from fastapi.testclient import TestClient
from pathlib import Path
import os

from api.main import app


def test_missing_dogs_endpoint_reads_file(tmp_path, monkeypatch):
    import asyncio
    from api.main import get_missing_dogs

    # Prepare a temporary missing_dogs.txt in the expected public path
    project_root = Path(__file__).resolve().parents[1]
    public_dir = project_root / 'react-app' / 'public'
    public_dir.mkdir(parents=True, exist_ok=True)
    file_path = public_dir / 'missing_dogs.txt'

    content = """Missing dogs (ID: Name):
12345: Test Dog
23456: Another Dog
"""
    file_path.write_text(content, encoding='utf-8')

    # Call the function directly
    api_resp = asyncio.run(get_missing_dogs())
    assert api_resp.success
    data = api_resp.data
    assert isinstance(data, list)
    assert any(d.get('id') == 12345 and d.get('name') == 'Test Dog' for d in data)
    assert any(d.get('id') == 23456 and d.get('name') == 'Another Dog' for d in data)

    # Cleanup
    file_path.unlink()
