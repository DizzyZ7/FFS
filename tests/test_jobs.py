import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import main

client=TestClient(main.app)

def test_generation_jobs_queue_and_cancel():
    pid='f'*32
    with tempfile.TemporaryDirectory() as d:
        folder=Path(d)/pid
        folder.mkdir()
        (folder/'shot-plan.json').write_text(json.dumps({
            'shots':[{'id':'shot-0001','prompt':'cinematic orbit'}]
        }))
        with patch.object(main,'ROOT',Path(d)):
            base='/api/projects/'+pid+'/generation/jobs'
            invalid=client.post(base,params={'shot_id':'shot-9999'})
            assert invalid.status_code==404
            response=client.post(base,params={'shot_id':'shot-0001'})
            assert response.status_code==200,response.text
            job=response.json()
            assert job['status']=='queued'
            assert client.get(base+'/'+job['id']).json()['status']=='queued'
            assert len(client.get(base).json()['jobs'])==1
            cancelled=client.post(base+'/'+job['id']+'/cancel')
            assert cancelled.status_code==200
            assert cancelled.json()['status']=='cancelled'
            assert client.post(base+'/'+job['id']+'/cancel').status_code==409
