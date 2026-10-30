"""Deterministic speech-based cut planning; no external model required."""
from math import isfinite

def plan_speech_cuts(words, duration:float, min_pause:float=0.65,
                     padding:float=0.18, min_clip:float=0.25):
    """Return sorted non-overlapping keep ranges in source-video seconds.

    Only gaps between detected words are cut; leading/trailing silence is trimmed.
    """
    if not isfinite(duration) or duration<=0:
        raise ValueError('Invalid source duration')
    if not isfinite(min_pause) or min_pause<0.1 or min_pause>10:
        raise ValueError('Invalid pause threshold')
    if not isfinite(padding) or padding<0 or padding>2:
        raise ValueError('Invalid speech padding')
    if not isfinite(min_clip) or min_clip<=0:
        raise ValueError('Invalid minimum clip length')
    if not words:
        return []
    intervals=[]
    last_start=-1.0
    for item in words:
        start=float(item['start'])
        end=float(item['end'])
        if not (isfinite(start) and isfinite(end) and 0<=start<end<=duration+0.05):
            raise ValueError('Invalid word timestamp')
        if start<last_start:
            raise ValueError('Words must be chronological')
        last_start=start
        intervals.append((max(0,start-padding),min(duration,end+padding)))
    merged=[]
    for start,end in intervals:
        if merged and start-merged[-1][1]<min_pause:
            merged[-1][1]=max(merged[-1][1],end)
        else:
            merged.append([start,end])
    result=[]
    for start,end in merged:
        if end-start<min_clip:
            if result:
                result[-1]['end']=end
            continue
        result.append({'start':round(start,3),'end':round(end,3)})
    return result
