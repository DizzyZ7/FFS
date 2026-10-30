"""Reference-faithful output settings and optional licensed soundtrack preservation."""
import math
import subprocess
from pathlib import Path

def reference_output_settings(blueprint:dict):
    reference=blueprint.get('reference',{})
    width=int(reference.get('width') or 1280)
    height=int(reference.get('height') or 720)
    fps_value=str(reference.get('fps') or '30/1')
    try:
        if '/' in fps_value:
            numerator,denominator=(float(x) for x in fps_value.split('/',1))
            fps=numerator/denominator
        else:
            fps=float(fps_value)
    except (ValueError,ZeroDivisionError):
        fps=30.0
    if not (16<=width<=3840 and 16<=height<=2160 and width%2==0 and height%2==0):
        raise ValueError('Invalid reference dimensions')
    if not math.isfinite(fps) or not 1<=fps<=120:
        raise ValueError('Invalid reference FPS')
    return width,height,round(fps,3)

def mux_reference_audio(folder:Path,silent_video:Path,output:Path):
    """Add the reference soundtrack without looping it; silent sources stay silent."""
    source=folder/'source.mp4'
    if not source.is_file():
        raise FileNotFoundError('Reference source missing')
    args=['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',
          '-i',str(silent_video),'-i',str(source),
          '-map','0:v:0','-map','1:a:0?','-c:v','copy',
          '-c:a','aac','-b:a','192k',
          '-shortest','-movflags','+faststart',str(output)]
    subprocess.run(args,check=True,capture_output=True,text=True,timeout=600)
    return output
