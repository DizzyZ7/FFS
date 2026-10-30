from fastapi.testclient import TestClient
from app import main
import json

def test_dispatch_reservation_endpoint(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'ROOT',tmp_path)
    pid='a'*32
    folder=tmp_path/pid
    folder.mkdir()
    blueprint={'reference':{},'shots':[{'id':'shot-0001','duration':2,
        'source_start':0,'source_end':2,'instructions':'Sunrise',
        'subject_ids':[],'revision':0,'generation_status':'not_generated'}]}
    (folder/'recreation-blueprint.json').write_text(json.dumps(blueprint))
    client=TestClient(main.app)
    payload={'shot_id':'shot-0001','idempotency_key':'request-12345678'}
    first=client.post(f'/api/projects/{pid}/recreation/dispatch-reservations',json=payload)
    second=client.post(f'/api/projects/{pid}/recreation/dispatch-reservations',json=payload)
    assert first.status_code==200,first.text
    assert first.json()['created'] is True
    assert second.json()['created'] is False
    assert client.get(f'/api/projects/{pid}/recreation/dispatch-reservations/request-12345678').status_code==200
