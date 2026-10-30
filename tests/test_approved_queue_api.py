import json
from fastapi.testclient import TestClient
from app import main

def test_approved_queue_endpoint(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'ROOT',tmp_path)
    pid='b'*32
    folder=tmp_path/pid
    folder.mkdir()
    blueprint={'shots':[{'id':'shot-0001','duration':2,'source_start':0,
        'source_end':2,'instructions':'Sunrise','subject_ids':[],
        'revision':0,'generation_status':'not_generated'}]}
    (folder/'recreation-blueprint.json').write_text(json.dumps(blueprint))
    client=TestClient(main.app)
    data={'shot_id':'shot-0001','idempotency_key':'request-12345678',
          'price_per_second_usd':2,'approved':True,'max_budget_usd':4}
    path=f'/api/projects/{pid}/recreation/approved-queue'
    first=client.post(path,json=data)
    assert first.status_code==200,first.text
    second=client.post(path,json=data)
    assert second.status_code==200,second.text
    assert first.json()['job']['id']==second.json()['job']['id']
    assert second.json()['reservation']['created'] is False
