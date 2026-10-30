import json
from fastapi.testclient import TestClient
from app import main

def test_sqlite_journal_api_replay_and_legacy_conflict(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'ROOT',tmp_path)
    pid='c'*32
    folder=tmp_path/pid
    folder.mkdir()
    blueprint={'shots':[{'id':'shot-0001','duration':2,'source_start':0,
        'source_end':2,'instructions':'Sunrise','subject_ids':[],
        'revision':0,'generation_status':'not_generated'}]}
    (folder/'recreation-blueprint.json').write_text(json.dumps(blueprint))
    client=TestClient(main.app)
    data={'shot_id':'shot-0001','idempotency_key':'journal-12345678',
          'price_per_second_usd':2,'approved':True,'max_budget_usd':4}
    url=f'/api/projects/{pid}/recreation/approved-sqlite-journal'
    first=client.post(url,json=data)
    assert first.status_code==200,first.text
    assert first.json()['runnable'] is False
    second=client.post(url,json=data)
    assert second.status_code==200,second.text
    assert first.json()['job']['id']==second.json()['job']['id']
    assert second.json()['created'] is False
    assert not (folder/'generation-jobs').exists()
    denied=client.post(url,json={**data,'idempotency_key':'denied-12345678','approved':False})
    assert denied.status_code==403
