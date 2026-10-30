import pytest
from app import jobs
from app.worker import execute_job
from app.generation import GenerationRequest,GenerationResult,JobStatus,DisabledProvider

def request(shot='shot-0001'):
    return GenerationRequest(project_id='test',shot_id=shot,prompt='A cinematic shot',duration_seconds=2)

def test_job_lifecycle(tmp_path):
    job=jobs.enqueue(tmp_path,'shot-0001')
    assert jobs.claim(tmp_path,job['id'])['status']=='running'
    assert jobs.complete(tmp_path,job['id'],error='provider failed')['status']=='failed'
    with pytest.raises(ValueError):
        jobs.complete(tmp_path,job['id'],error='again')

def test_disabled_provider_does_not_claim(tmp_path):
    job=jobs.enqueue(tmp_path,'shot-0001')
    with pytest.raises(RuntimeError):
        execute_job(tmp_path,job['id'],request(),DisabledProvider())
    assert jobs.get_job(tmp_path,job['id'])['status']=='queued'

def test_provider_success(tmp_path):
    output=tmp_path/'generated'/'shot.mp4';output.parent.mkdir()
    output.write_bytes(b'placeholder')
    class Provider:
        provider_id='mock'
        def generate(self,req):
            return GenerationResult(status=JobStatus.succeeded,output_path=str(output))
    job=jobs.enqueue(tmp_path,'shot-0001')
    result=execute_job(tmp_path,job['id'],request(),Provider())
    assert result['status']=='succeeded'
    assert result['output_path']=='generated/shot.mp4'

def test_output_cannot_escape_project(tmp_path):
    output=tmp_path.parent/'outside.mp4';output.write_bytes(b'placeholder')
    class Provider:
        provider_id='mock'
        def generate(self,req):
            return GenerationResult(status=JobStatus.succeeded,output_path=str(output))
    job=jobs.enqueue(tmp_path,'shot-0001')
    with pytest.raises(ValueError):
        execute_job(tmp_path,job['id'],request(),Provider())
    assert jobs.get_job(tmp_path,job['id'])['status']=='failed'
