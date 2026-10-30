import json
import re
import subprocess
from pathlib import Path

def run(args, timeout=180):
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=timeout)

def probe(path: Path):
    data = json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]).stdout)
    video = next((s for s in data.get('streams',[]) if s.get('codec_type')=='video'), None)
    if video is None:
        raise ValueError('No video stream')
    return {'duration':float(data['format'].get('duration') or video.get('duration') or 0),
            'width':video.get('width'), 'height':video.get('height'),
            'fps':video.get('avg_frame_rate'), 'codec':video.get('codec_name')}

def detect_scenes(path: Path, duration: float, threshold=0.30):
    result = subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-vf',f"select='gt(scene,{threshold})',showinfo",'-an','-f','null','-'],capture_output=True,text=True,timeout=300)
    if result.returncode != 0:
        raise RuntimeError('Scene detection failed')
    times=[]
    for line in result.stderr.splitlines():
        if 'showinfo' in line:
            match=re.search(r'pts_time:\s*([\d.]+)',line)
            if match:
                t=float(match.group(1))
                if 0.1<t<duration-0.1 and (not times or t-times[-1]>0.25):
                    times.append(t)
    edges=[0.0]+times+[duration]
    return [{'start':round(a,3),'end':round(b,3)} for a,b in zip(edges,edges[1:]) if b-a>=0.05]

def render(source: Path, clips: list, output: Path):
    if not clips:
        raise ValueError('Timeline is empty')
    meta=probe(source)
    duration=meta['duration']
    if len(clips)>100:
        raise ValueError('Too many clips')
    filters=[]; labels=[]
    for i,clip in enumerate(clips):
        start=float(clip['start']); end=float(clip['end'])
        if not (0<=start<end<=duration+0.01):
            raise ValueError('Invalid clip bounds')
        filters.append(f'[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=30,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v{i}]')
        labels.append(f'[v{i}]')
    filters.append(''.join(labels)+f'concat=n={len(clips)}:v=1:a=0[outv]')
    run(['ffmpeg','-y','-i',str(source),'-filter_complex',';'.join(filters),'-map','[outv]','-c:v','libx264','-preset','veryfast','-crf','23','-movflags','+faststart',str(output)],timeout=1800)
    return output

def render_social(source: Path, clips: list, output: Path, aspect: str='9:16',
                  framing: str='crop'):
    """Render normalized social video from source clips, preserving source audio if present."""
    presets={'9:16':(720,1280),'1:1':(720,720),'16:9':(1280,720)}
    if aspect not in presets or framing not in ('crop','pad'):
        raise ValueError('Unsupported aspect ratio or framing')
    if not clips or len(clips)>100:
        raise ValueError('Expected 1-100 clips')
    meta=probe(source)
    width,height=presets[aspect]
    video_filters=[];audio_filters=[];vlabels=[];alabels=[]
    for i,clip in enumerate(clips):
        start=float(clip['start']);end=float(clip['end'])
        if not (0<=start<end<=meta['duration']+0.01):
            raise ValueError('Invalid clip bounds')
        scale_mode='increase' if framing=='crop' else 'decrease'
        geometry=(f'crop={width}:{height}' if framing=='crop'
                  else f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2')
        video_filters.append(
            f'[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,'
            f'fps=30,scale={width}:{height}:force_original_aspect_ratio={scale_mode},'
            f'{geometry},setsar=1,format=yuv420p[v{i}]')
        vlabels.append(f'[v{i}]')
    video_filters.append(''.join(vlabels)+f'concat=n={len(clips)}:v=1:a=0[outv]')
    # Build video first; audio is handled by a separate filtergraph when present.
    has_audio=False
    try:
        streams=json.loads(run(['ffprobe','-v','error','-show_streams','-of','json',str(source)]).stdout)
        has_audio=any(x.get('codec_type')=='audio' for x in streams.get('streams',[]))
    except (ValueError,KeyError):
        pass
    if has_audio:
        for i,clip in enumerate(clips):
            audio_filters.append(
                f"[0:a:0]atrim=start={float(clip['start'])}:end={float(clip['end'])},"
                f'asetpts=PTS-STARTPTS[a{i}]')
            alabels.append(f'[a{i}]')
        audio_filters.append(''.join(alabels)+f'concat=n={len(clips)}:v=0:a=1[outa]')
    args=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),
          '-filter_complex',';'.join(video_filters+audio_filters),'-map','[outv]']
    if has_audio:
        args+=['-map','[outa]','-c:a','aac','-b:a','160k']
    args+=['-c:v','libx264','-preset','veryfast','-crf','23',
           '-movflags','+faststart',str(output)]
    run(args,timeout=1800)
    return output
