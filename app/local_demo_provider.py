"""Explicit local reference-clip demo provider.

This does NOT generate AI video. It cuts the corresponding portion of the
uploaded reference so the entire queue/worker/accept/render pipeline can be
exercised without API keys or GPU.
"""
import math
import re
import subprocess
from pathlib import Path
from .generation import GenerationResult,JobStatus

class LocalReferenceDemoProvider:
    provider_id='local-reference-demo'

    def __init__(self,project_folder:Path):
        self.folder=project_folder.resolve()

    def generate(self,request):
        request.validate()
        settings=request.settings
        start=float(settings['source_start'])
        end=float(settings['source_end'])
        if not math.isfinite(start) or not math.isfinite(end) or not 0<=start<end:
            raise ValueError('Invalid reference time range')
        if abs((end-start)-request.duration_seconds)>0.05:
            raise ValueError('Reference duration mismatch')
        job_id=settings['job_id']
        if not re.fullmatch(r'[0-9a-f]{32}',job_id):
            raise ValueError('Invalid job identifier')
        source=self.folder/'source.mp4'
        if not source.is_file():
            raise FileNotFoundError('Source video is missing')
        output_dir=self.folder/'generated'
        output_dir.mkdir(exist_ok=True)
        output=output_dir/(job_id+'.mp4')
        partial=output_dir/(job_id+'.partial.mp4')
        try:
            subprocess.run([
                'ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',
                '-ss',str(start),'-i',str(source),'-t',str(end-start),
                '-map','0:v:0','-an','-vf','fps=30,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1',
                '-c:v','libx264','-preset','veryfast','-crf','23',
                '-movflags','+faststart',str(partial)
            ],check=True,capture_output=True,text=True,timeout=180)
            if not partial.is_file() or partial.stat().st_size==0:
                raise RuntimeError('FFmpeg produced no video')
            partial.replace(output)
        finally:
            partial.unlink(missing_ok=True)
        return GenerationResult(status=JobStatus.succeeded,output_path=str(output))
