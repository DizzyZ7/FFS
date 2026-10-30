"""CPU-only audio onset and cut alignment analysis, no external ML service."""
import json
import math
import subprocess
from pathlib import Path

def _audio_samples(source:Path, sample_rate=8000, timeout=120):
    probe=subprocess.run(['ffprobe','-v','error','-select_streams','a:0',
                          '-show_entries','stream=index','-of','json',str(source)],
                         check=True,capture_output=True,text=True,timeout=30)
    if not json.loads(probe.stdout).get('streams'):
        return []
    decoded=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-loglevel','error',
                            '-i',str(source),'-map','0:a:0','-vn','-ac','1',
                            '-ar',str(sample_rate),'-f','f32le','-'],
                           check=True,capture_output=True,timeout=timeout)
    from array import array
    samples=array('f')
    samples.frombytes(decoded.stdout)
    return samples

def audio_onsets(source:Path,*,window_ms=50,max_seconds=600):
    """Detect strong positive short-term RMS changes (onset candidates, not BPM)."""
    if not 20<=window_ms<=200:
        raise ValueError('Window must be 20-200 ms')
    samples=_audio_samples(source)
    if not samples:
        return {'has_audio':False,'onsets':[],'method':'rms_energy_change'}
    rate=8000;step=int(rate*window_ms/1000)
    levels=[]
    for offset in range(0,min(len(samples),rate*max_seconds),step):
        segment=samples[offset:offset+step]
        if not segment:
            break
        levels.append(math.sqrt(sum(float(x)*float(x) for x in segment)/len(segment)))
    if len(levels)<4:
        return {'has_audio':True,'onsets':[],'method':'rms_energy_change'}
    changes=[max(0.0,levels[i]-levels[i-1]) for i in range(1,len(levels))]
    positives=sorted(x for x in changes if x>0)
    if not positives:
        return {'has_audio':True,'onsets':[],'method':'rms_energy_change'}
    median=positives[len(positives)//2]
    threshold=max(median*3,0.008)
    candidates=[]
    for i,delta in enumerate(changes):
        if delta>=threshold and (i==0 or delta>=changes[i-1]) and (i==len(changes)-1 or delta>=changes[i+1]):
            timestamp=round((i+1)*step/rate,3)
            if not candidates or timestamp-candidates[-1]>=0.18:
                candidates.append(timestamp)
    return {'has_audio':True,'onsets':candidates[:500],
            'method':'rms_energy_change','window_ms':window_ms}

def cut_alignment(cut_points,onsets,*,tolerance=0.12):
    """Nearest onset per cut; null means no onset within tolerance."""
    if not 0<tolerance<=1:
        raise ValueError('Invalid tolerance')
    matches=[]
    for point in cut_points:
        point=float(point)
        nearest=min(onsets,key=lambda x:abs(x-point)) if onsets else None
        delta=round(nearest-point,3) if nearest is not None else None
        matches.append({'cut_time':point,'nearest_onset':nearest if delta is not None and abs(delta)<=tolerance else None,
                        'offset_seconds':delta if delta is not None and abs(delta)<=tolerance else None})
    return {'cuts':matches,'aligned_count':sum(x['nearest_onset'] is not None for x in matches),
            'total_cuts':len(matches),'tolerance_seconds':tolerance}
