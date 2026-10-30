"""Low-cost, explainable visual scene quality signals using FFmpeg stats.

No GPU or external ML models required. This is not object/emotion detection.
"""
import math
import re
import subprocess
from pathlib import Path

def parse_signal_log(stderr: str):
    values=[]
    for line in stderr.splitlines():
        # signalstats writes metadata such as lavfi.signalstats.YAVG=...
        match=re.search(r'lavfi\.signalstats\.YAVG\s*[:=]\s*([0-9.]+)',line)
        if match:
            values.append(float(match.group(1)))
    return values

def score_brightness(samples):
    if not samples:
        return 0.0
    mean=sum(samples)/len(samples)
    # Reward exposure near middle-gray; penalize heavily under/overexposed clips.
    return round(max(0.0,1.0-abs(mean-128.0)/128.0),4)

def visual_scene_scores(source: Path, scenes: list, *, duration: float,
                        sample_fps: float=1.0):
    if not math.isfinite(duration) or duration<=0:
        raise ValueError('Invalid video duration')
    if not 0.1<=sample_fps<=2:
        raise ValueError('Invalid sample rate')
    if len(scenes)>100:
        raise ValueError('Too many scenes')
    results=[]
    for i,scene in enumerate(scenes):
        start=float(scene['start']);end=float(scene['end'])
        if not all(map(math.isfinite,(start,end))) or not 0<=start<end<=duration+0.05:
            raise ValueError('Invalid scene bounds')
        # metadata=print sends signalstats per-frame to stderr, no intermediate files.
        command=['ffmpeg','-hide_banner','-nostdin','-loglevel','info','-ss',str(start),
                 '-t',str(min(end,duration)-start),'-i',str(source),
                 '-vf',f'fps={sample_fps},signalstats,metadata=print',
                 '-an','-f','null','-']
        try:
            result=subprocess.run(command,capture_output=True,text=True,
                                  timeout=45,check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError('Visual analysis timed out') from exc
        if result.returncode:
            raise RuntimeError('FFmpeg visual analysis failed')
        samples=parse_signal_log(result.stderr)
        results.append({'source_index':i,'start':round(start,3),'end':round(end,3),
                        'brightness_score':score_brightness(samples),
                        'sample_count':len(samples)})
    return results
