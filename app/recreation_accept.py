"""Attach completed generation jobs to their exact recreation shot revisions."""
import json
import os
import uuid
from pathlib import Path
from . import jobs
from .recreation_jobs import mark_shot_generated

def accept_completed_job(folder:Path,job_id:str):
    job=jobs.get_job(folder,job_id)
    if job['status']!='succeeded' or not job.get('output_path'):
        raise ValueError('Generation job is not successful')
    if not job.get('fingerprint'):
        raise ValueError('Job has no recreation revision fingerprint')
    root=folder.resolve()
    generated=(root/'generated').resolve()
    output=(root/job['output_path']).resolve()
    if not output.is_relative_to(generated) or output.suffix.lower()!='.mp4' or not output.is_file():
        raise ValueError('Generated MP4 is missing or outside the project')
    blueprint_path=folder/'recreation-blueprint.json'
    blueprint=json.loads(blueprint_path.read_text(encoding='utf8'))
    revised=mark_shot_generated(blueprint,job['shot_id'],
                               fingerprint=job['fingerprint'],
                               output_path=str(output.relative_to(root)))
    temp=blueprint_path.with_name(blueprint_path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temp.write_text(json.dumps(revised,ensure_ascii=False,indent=2),encoding='utf8')
        os.replace(temp,blueprint_path)
    finally:
        temp.unlink(missing_ok=True)
    return {'shot_id':job['shot_id'],'job_id':job_id,
            'output_path':str(output.relative_to(root)),
            'revision':next(s['revision'] for s in revised['shots'] if s['id']==job['shot_id'])}
