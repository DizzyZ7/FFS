"""Persistent, local-only generation job queue. No external model calls.

The queue records pending work and supports cancellation. Workers are intentionally
not started until an explicit provider is configured in a future release.
"""
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

_lock=threading.RLock()
VALID_STATES={'queued','running','succeeded','failed','cancelled'}
TERMINAL={'succeeded','failed','cancelled'}

def _now():
    return datetime.now(timezone.utc).isoformat()

def _read(path:Path):
    return json.loads(path.read_text(encoding='utf8'))

def _write(path:Path,payload:dict):
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temp.write_text(json.dumps(payload),encoding='utf8')
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)

def enqueue(folder:Path,shot_id:str):
    with _lock:
        jobs=folder/'generation-jobs'
        jobs.mkdir(exist_ok=True)
        job_id=uuid.uuid4().hex
        job={'id':job_id,'shot_id':shot_id,'status':'queued',
             'created_at':_now(),'updated_at':_now(),'progress':0,
             'output_path':None,'error':None}
        _write(jobs/(job_id+'.json'),job)
        return job

def get_job(folder:Path,job_id:str):
    if len(job_id)!=32 or any(c not in '0123456789abcdef' for c in job_id):
        raise ValueError('Invalid job ID')
    path=folder/'generation-jobs'/(job_id+'.json')
    if not path.is_file():
        raise FileNotFoundError(job_id)
    return _read(path)

def list_jobs(folder:Path):
    jobs=folder/'generation-jobs'
    if not jobs.is_dir():
        return []
    return sorted((_read(path) for path in jobs.glob('*.json')),
                  key=lambda item:item['created_at'],reverse=True)

def cancel(folder:Path,job_id:str):
    with _lock:
        job=get_job(folder,job_id)
        if job['status']!='queued':
            raise ValueError('Only queued jobs can be cancelled')
        job['status']='cancelled'
        job['updated_at']=_now()
        _write(folder/'generation-jobs'/(job_id+'.json'),job)
        return job

def claim(folder:Path,job_id:str):
    """Atomically transition a queued job to running within this process."""
    with _lock:
        job=get_job(folder,job_id)
        if job['status']!='queued':
            raise ValueError('Job is not queued')
        job['status']='running'
        job['updated_at']=_now()
        _write(folder/'generation-jobs'/(job_id+'.json'),job)
        return job

def complete(folder:Path,job_id:str,*,output_path:str|None=None,error:str|None=None):
    with _lock:
        job=get_job(folder,job_id)
        if job['status']!='running':
            raise ValueError('Job is not running')
        if bool(output_path)==bool(error):
            raise ValueError('Exactly one of output_path or error is required')
        job['status']='succeeded' if output_path else 'failed'
        job['progress']=100 if output_path else job['progress']
        job['output_path']=output_path
        job['error']=error
        job['updated_at']=_now()
        _write(folder/'generation-jobs'/(job_id+'.json'),job)
        return job
