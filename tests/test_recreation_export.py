import json
from fastapi.testclient import TestClient
import app.main as main
from app.recreation_export import export_fingerprint

def test_fingerprint_changes_with_revision_and_clip():
    base={'shots':[{'id':'a','revision':0,'duration':2,'instructions':'a',
                    'subject_ids':[],'generation_status':'succeeded',
                    'output_path':'generated/a.mp4'}]}
    changed=json.loads(json.dumps(base))
    changed['shots'][0]['revision']=1
    assert export_fingerprint(base)!=export_fingerprint(changed)
    changed=json.loads(json.dumps(base))
    changed['shots'][0]['output_path']='generated/b.mp4'
    assert export_fingerprint(base)!=export_fingerprint(changed)

def test_download_rejects_outdated_recreation(tmp_path,monkeypatch):
    pid='e'*32;folder=tmp_path/pid;folder.mkdir()
    monkeypatch.setattr(main,'ROOT',tmp_path)
    blueprint={'shots':[{'id':'a','revision':1,'duration':2,'instructions':'changed',
                         'subject_ids':[],'generation_status':'succeeded',
                         'output_path':'generated/a.mp4'}]}
    (folder/'recreation-blueprint.json').write_text(json.dumps(blueprint))
    (folder/'recreation-final.mp4').write_bytes(b'old video')
    (folder/'recreation-final.fingerprint').write_text('outdated')
    response=TestClient(main.app).get(f'/api/projects/{pid}/recreation/download')
    assert response.status_code==409
