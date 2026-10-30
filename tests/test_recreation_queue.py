from fastapi.testclient import TestClient
from app import jobs
from app.main import app
import app.main as main_module
import json
import pytest

def test_queue_recreation_revision_is_idempotent(tmp_path,monkeypatch):
    pid='a'*32
    folder=tmp_path/pid;folder.mkdir()
    monkeypatch.setattr(main_module,'ROOT',tmp_path)
    blueprint={'shots':[{'id':'shot-0001','duration':2,'subject_ids':[],
                          'instructions':'Cinematic view','revision':0,
                          'generation_status':'not_generated','output_path':None}]}
    (folder/'recreation-blueprint.json').write_text(json.dumps(blueprint))
    client=TestClient(app)
    endpoint=f'/api/projects/{pid}/recreation/shots/shot-0001/queue'
    first=client.post(endpoint)
    second=client.post(endpoint)
    assert first.status_code==200
    assert first.json()['id']==second.json()['id']
    assert len(jobs.list_jobs(folder))==1
    assert len(client.get(f'/api/projects/{pid}/recreation/pending').json()['shots'])==1

def test_queue_requires_instructions(tmp_path,monkeypatch):
    pid='b'*32;folder=tmp_path/pid;folder.mkdir()
    monkeypatch.setattr(main_module,'ROOT',tmp_path)
    (folder/'recreation-blueprint.json').write_text(json.dumps({'shots':[{
        'id':'shot-0001','duration':2,'subject_ids':[],
        'instructions':'','revision':0}]}))
    response=TestClient(app).post(f'/api/projects/{pid}/recreation/shots/shot-0001/queue')
    assert response.status_code==422
