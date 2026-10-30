"""Render an ordered reference recreation from accepted per-shot MP4 clips.

CPU-only FFmpeg normalization. Audio is intentionally not included in v1.
"""
import math
import subprocess
from pathlib import Path

def collect_recreation_clips(folder:Path,blueprint:dict):
    shots=blueprint.get('shots',[])
    if not shots or len(shots)>100:
        raise ValueError('Expected 1-100 shots')
    root=folder.resolve()
    generated=(root/'generated').resolve()
    clips=[]
    for shot in shots:
        if shot.get('generation_status')!='succeeded' or not shot.get('output_path'):
            raise ValueError('All shots must have accepted generated video')
        path=(root/shot['output_path']).resolve()
        if not path.is_relative_to(generated) or path.suffix.lower()!='.mp4' or not path.is_file():
            raise ValueError('Invalid generated clip path')
        duration=float(shot['duration'])
        if not math.isfinite(duration) or not 0<duration<=60:
            raise ValueError('Invalid shot duration')
        clips.append((path,duration))
    return clips

def render_recreation(folder:Path,blueprint:dict,output:Path):
    clips=collect_recreation_clips(folder,blueprint)
    output=output.resolve()
    if not output.is_relative_to(folder.resolve()):
        raise ValueError('Output must be inside project')
    filters=[];inputs=[]
    for index,(path,duration) in enumerate(clips):
        inputs.extend(['-i',str(path)])
        filters.append(
            f'[{index}:v:0]setpts=PTS-STARTPTS,'
            f'fps=30,scale=1280:720:force_original_aspect_ratio=decrease,'
            f'pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,'
            f'tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration},setpts=PTS-STARTPTS[v{index}]')
    filters.append(''.join(f'[v{i}]' for i in range(len(clips)))+
                   f'concat=n={len(clips)}:v=1:a=0[outv]')
    args=['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',*inputs,
          '-filter_complex',';'.join(filters),'-map','[outv]',
          '-c:v','libx264','-preset','veryfast','-crf','23',
          '-movflags','+faststart',str(output)]
    subprocess.run(args,check=True,capture_output=True,text=True,timeout=1800)
    return output
