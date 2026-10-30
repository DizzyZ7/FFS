import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import main

client=TestClient(main.app)

def test_save_and_reopen_timeline():
    with tempfile.TemporaryDirectory() as d:
        pid='b'*32
        folder=Path(d)/pid
        folder.mkdir()
        (folder/'project.json').write_text(json.dumps({
            'id':pid,'metadata':{'duration':10.0},'scenes':[],
            'timeline':[],'revision':1
        }))
        with patch.object(main,'ROOT',Path(d)):
            response=client.put('/api/projects/'+pid+'/timeline',json={
                'clips':[{'start':1,'end':3},{'start':5,'end':8}]
            })
            assert response.status_code==200,response.text
            assert response.json()['revision']==2
            saved=client.get('/api/projects/'+pid)
            assert saved.json()['timeline']==[{'start':1.0,'end':3.0},{'start':5.0,'end':8.0}]
            invalid=client.put('/api/projects/'+pid+'/timeline',json={
                'clips':[{'start':9,'end':11}]
            })
            assert invalid.status_code==422
            assert client.get('/api/projects/'+pid).json()['revision']==2
