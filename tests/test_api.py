import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import main

client=TestClient(main.app)

def test_health_endpoint():
    response=client.get('/api/health')
    assert response.status_code==200
    assert response.json()['status']=='ok'

def test_invalid_project_id():
    response=client.get('/api/projects/../../etc/passwd')
    assert response.status_code in (400,404)

def test_missing_project():
    response=client.get('/api/projects/'+'0'*32)
    assert response.status_code==404

def test_project_read():
    import json
    with tempfile.TemporaryDirectory() as d:
        project_id='a'*32
        folder=Path(d)/project_id
        folder.mkdir()
        payload={'id':project_id,'scenes':[{'start':0,'end':1}]}
        (folder/'project.json').write_text(json.dumps(payload))
        with patch.object(main,'ROOT',Path(d)):
            response=client.get('/api/projects/'+project_id)
        assert response.status_code==200
        assert response.json()==payload
