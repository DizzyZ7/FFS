import json
import pytest
from app import jobs
from app.recreation_jobs import shot_fingerprint
from app.recreation_accept import accept_completed_job

def setup(tmp_path):
    shot={'id':'shot-0001','duration':2,'instructions':'Cinematic',
          'subject_ids':[],'revision':0,'generation_status':'not_generated',
          'output_path':None}
    blueprint={'shots':[shot]}
    (tmp_path/'recreation-blueprint.json').write_text(json.dumps(blueprint))
    output=tmp_path/'generated'/'shot.mp4';output.parent.mkdir()
    output.write_bytes(b'test')
    job=jobs.enqueue(tmp_path,'shot-0001',fingerprint=shot_fingerprint(shot))
    jobs.claim(tmp_path,job['id'])
    jobs.complete(tmp_path,job['id'],output_path='generated/shot.mp4')
    return job,output

def test_accept_completed_job(tmp_path):
    job,_=setup(tmp_path)
    result=accept_completed_job(tmp_path,job['id'])
    assert result['output_path']=='generated/shot.mp4'
    data=json.loads((tmp_path/'recreation-blueprint.json').read_text())
    assert data['shots'][0]['generation_status']=='succeeded'

def test_reject_stale_revision(tmp_path):
    job,_=setup(tmp_path)
    path=tmp_path/'recreation-blueprint.json'
    data=json.loads(path.read_text());data['shots'][0]['revision']=1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='changed'):
        accept_completed_job(tmp_path,job['id'])
    assert json.loads(path.read_text())['shots'][0]['output_path'] is None

def test_reject_missing_video(tmp_path):
    job,output=setup(tmp_path);output.unlink()
    with pytest.raises(ValueError,match='missing'):
        accept_completed_job(tmp_path,job['id'])
