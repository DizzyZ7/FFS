"""Reference analysis helpers using local FFmpeg tools only.

Outputs a stable, versioned shot plan without uploading user media.
"""
import json
import math
import subprocess
from pathlib import Path
from .media import probe, detect_scenes

SCHEMA_VERSION=1

def _validate_threshold(value):
    value=float(value)
    if not math.isfinite(value) or not 0.01 <= value <= 0.95:
        raise ValueError('threshold must be between 0.01 and 0.95')
    return value

def reference_plan(path:Path,threshold:float=0.30):
    threshold=_validate_threshold(threshold)
    metadata=probe(path)
    duration=float(metadata['duration'])
    if not math.isfinite(duration) or duration<=0:
        raise ValueError('invalid video duration')
    scenes=detect_scenes(path,duration,threshold)
    shots=[]
    for i,scene in enumerate(scenes):
        start=float(scene['start']);end=float(scene['end'])
        shots.append({
            'id':f'shot-{i+1:04d}',
            'start':start,'end':end,'duration':round(end-start,3),
            'source':'reference','subject_ids':[],
            'prompt':'','status':'not_generated'
        })
    return {'schema_version':SCHEMA_VERSION,'reference':metadata,
            'shots':shots,'total_duration':duration,
            'analysis':{'scene_threshold':threshold,'shot_count':len(shots)}}

def extract_contact_sheet_frames(path:Path,output_dir:Path,shots:list,max_frames:int=30):
    """Extract one representative frame per shot, capped to avoid disk exhaustion."""
    output_dir.mkdir(parents=True,exist_ok=True)
    paths=[]
    for i,shot in enumerate(shots[:max_frames]):
        midpoint=(float(shot['start'])+float(shot['end']))/2
        dest=output_dir/f'shot-{i+1:04d}.jpg'
        proc=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
            '-ss',str(midpoint),'-i',str(path),'-frames:v','1',
            '-vf','scale=480:-2','-q:v','4',str(dest)],
            capture_output=True,text=True,timeout=60)
        if proc.returncode!=0 or not dest.is_file():
            raise RuntimeError('Could not extract reference frame')
        paths.append(dest.name)
    return paths
