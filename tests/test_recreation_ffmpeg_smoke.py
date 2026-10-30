"""Exercise real FFmpeg video assembly, not only mocked command arguments."""
import shutil
import subprocess
import pytest
from app.media import probe
from app.recreation_render import render_recreation

@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
                    reason='FFmpeg tools not installed')
def test_recreation_real_ffmpeg_assembly(tmp_path):
    generated=tmp_path/'generated'
    generated.mkdir()
    clips=[]
    for index,color in enumerate(('red','blue')):
        output=generated/f'{index}.mp4'
        subprocess.run([
            'ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',
            '-f','lavfi','-i',f'color=c={color}:s=160x90:r=15:d=0.35',
            '-an','-c:v','mpeg4',str(output)
        ],check=True,capture_output=True,timeout=30)
        clips.append({'duration':0.5,'generation_status':'succeeded',
                      'output_path':f'generated/{index}.mp4'})
    final=tmp_path/'recreation-final.mp4'
    render_recreation(tmp_path,{'shots':clips},final)
    metadata=probe(final)
    assert final.stat().st_size>0
    assert metadata['width']==1280 and metadata['height']==720
    assert 0.90<=metadata['duration']<=1.10
