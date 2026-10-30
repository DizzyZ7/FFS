import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import main

client=TestClient(main.app)

def test_shot_plan_persistence():
    pid='c'*32
    with tempfile.TemporaryDirectory() as d:
        folder=Path(d)/pid
        folder.mkdir()
        (folder/'shot-plan.json').write_text(json.dumps({
            'schema_version':1,
            'shots':[{'id':'shot-0001','prompt':'','subject_ids':[]}]
        }))
        with patch.object(main,'ROOT',Path(d)):
            response=client.put('/api/projects/'+pid+'/shot-plan',json={
                'shots':[{'shot_id':'shot-0001','prompt':'warm cinematic light','subject_ids':['hero']}]
            })
            assert response.status_code==200,response.text
            assert response.json()['revision']==1
            loaded=client.get('/api/projects/'+pid+'/shot-plan')
            assert loaded.json()['shots'][0]['prompt']=='warm cinematic light'
            invalid=client.put('/api/projects/'+pid+'/shot-plan',json={
                'shots':[{'shot_id':'shot-9999','prompt':'invalid'}]
            })
            assert invalid.status_code==422
            assert client.get('/api/projects/'+pid+'/shot-plan').json()['revision']==1
