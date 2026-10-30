"""CPU-only frame-difference activity for reference scenes.

Frame differences measure visual activity, not camera direction or optical flow.
"""
import math
import re
import subprocess
from pathlib import Path

def parse_scene_differences(stderr):
    """Read lavfi.scene_score metadata emitted by scdet."""
    scores=[]
    for line in stderr.splitlines():
        match=re.search(r'lavfi\.scd\.score\s*[:=]\s*([0-9.]+)',line)
        if match:
            scores.append(float(match.group(1)))
    return scores

def classify_activity(scores):
    if not scores:
        return 'unknown'
    mean=sum(scores)/len(scores)
    if mean<1.5:
        return 'low'
    if mean<5:
        return 'medium'
    return 'high'

def analyze_motion_activity(source:Path,scenes:list,*,duration:float,sample_fps=4):
    if not math.isfinite(duration) or not 0<duration<=600:
        raise ValueError('Invalid duration')
    if not 1<=sample_fps<=10 or len(scenes)>100:
        raise ValueError('Invalid sampling or scene count')
    output=[]
    for shot in scenes:
        start=float(shot['start']);end=float(shot['end'])
        if not math.isfinite(start) or not math.isfinite(end) or not 0<=start<end<=duration+0.05:
            raise ValueError('Invalid scene bounds')
        result=subprocess.run([
            'ffmpeg','-hide_banner','-nostdin','-loglevel','info',
            '-ss',str(start),'-t',str(end-start),'-i',str(source),
            '-vf',f'fps={sample_fps},scale=320:-2,scdet=threshold=10,metadata=print',
            '-an','-f','null','-'
        ],capture_output=True,text=True,timeout=45)
        if result.returncode:
            raise RuntimeError('Frame-difference analysis failed')
        scores=parse_scene_differences(result.stderr)
        output.append({'start':round(start,3),'end':round(end,3),
                       'visual_activity':classify_activity(scores),
                       'mean_difference_score':round(sum(scores)/len(scores),3) if scores else None,
                       'sample_count':len(scores),
                       'method':'ffmpeg_scdet_frame_difference',
                       'camera_motion':'unknown'})
    return output
