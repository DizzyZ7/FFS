"""Explicit, opt-in single-job execution against a configured generation provider.

No background worker is launched automatically. Providers must be injected by the
application operator. Output must be inside the project's generated directory.
"""
from pathlib import Path
from . import jobs
from .generation import GenerationRequest,JobStatus

def execute_job(folder:Path,job_id:str,request:GenerationRequest,provider):
    request.validate()
    if provider.provider_id=='disabled':
        raise RuntimeError('No video generation provider configured')
    if request.shot_id!=jobs.get_job(folder,job_id)['shot_id']:
        raise ValueError('Shot mismatch')
    jobs.claim(folder,job_id)
    try:
        result=provider.generate(request)
        if result.status!=JobStatus.succeeded or not result.output_path:
            return jobs.complete(folder,job_id,error=result.error or 'Provider did not generate video')
        output=Path(result.output_path).resolve()
        root=(folder/'generated').resolve()
        if not output.is_relative_to(root) or not output.is_file() or output.suffix.lower()!='.mp4':
            raise ValueError('Provider output must be an existing MP4 in project generated directory')
        return jobs.complete(folder,job_id,output_path=str(output.relative_to(folder.resolve())))
    except Exception as exc:
        jobs.complete(folder,job_id,error=f'Generation failed: {type(exc).__name__}')
        raise
