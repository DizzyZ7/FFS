"""Real FFmpeg pipeline smoke test: queue -> local demo -> accept -> assemble."""
import json
import shutil
import subprocess
import pytest
from fastapi.testclient import TestClient
import app.main as main
from app.recreation_jobs import shot_fingerprint

@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
                    reason='FFmpeg tools not installed')
def test_local_demo_full_recreation_pipeline(tmp_path,monkeypatch):
    pid='c'*32
    folder=tmp_path/pid
    folder.mkdir()
    monkeypatch.setattr(main,'ROOT',tmp_path)
    subprocess.run([
        'ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',
        '-f','lavfi','-i','color=c=blue:s=160x90:r=15:d=1',
        '-an','-c:v','mpeg4',str(folder/'source.mp4')
    ],check=True,capture_output=True,timeout=30)
    shot={'id':'shot-0001','duration':0.5,'source_start':0,
          'source_end':0.5,'subject_ids':[],'instructions':'Demo',
          'revision':0,'generation_status':'not_generated','output_path':None}
    (folder/'recreation-blueprint.json').write_text(json.dumps({'shots':[shot]}))
    client=TestClient(main.app)
    queued=client.post(f'/api/projects/{pid}/recreation/shots/shot-0001/queue')
    assert queued.status_code==200,queued.text
    job_id=queued.json()['id']
    completed=client.post(f'/api/projects/{pid}/recreation/jobs/{job_id}/run-local-demo')
    assert completed.status_code==200,completed.text
    assert completed.json()['mode']=='local_reference_demo'
    blueprint=client.get(f'/api/projects/{pid}/recreation/blueprint').json()
    assert blueprint['shots'][0]['generation_status']=='succeeded'
    rendered=client.post(f'/api/projects/{pid}/recreation/render')
    assert rendered.status_code==200,rendered.text
    assert (folder/'recreation-final.mp4').stat().st_size>0

def test_local_demo_rejects_stale_job_without_running(tmp_path,monkeypatch):
    from app import jobs
    pid='d'*32;folder=tmp_path/pid;folder.mkdir()
    monkeypatch.setattr(main,'ROOT',tmp_path)
    shot={'id':'shot-0001','duration':0.5,'source_start':0,'source_end':0.5,
          'subject_ids':[],'instructions':'new','revision':1}
    (folder/'recreation-blueprint.json').write_text(json.dumps({'shots':[shot]}))
    queued=jobs.enqueue(folder,'shot-0001',fingerprint='stale')
    response=TestClient(main.app).post(
        f'/api/projects/{pid}/recreation/jobs/{queued["id"]}/run-local-demo')
    assert response.status_code==409
    assert jobs.get_job(folder,queued['id'])['status']=='queued'
