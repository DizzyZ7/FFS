"""End-to-end media smoke test using a synthetic video (no external assets)."""
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.media import run, probe, detect_scenes, render

def main():
    with tempfile.TemporaryDirectory() as d:
        folder=Path(d)
        src=folder/'source.mp4'
        dst=folder/'output.mp4'
        run(['ffmpeg','-y','-f','lavfi','-i','testsrc2=size=320x240:rate=15',
             '-t','2','-c:v','libx264','-pix_fmt','yuv420p',str(src)])
        metadata=probe(src)
        assert 1.8 < metadata['duration'] < 2.2, metadata
        scenes=detect_scenes(src,metadata['duration'])
        assert scenes, 'No scenes detected'
        render(src,[{'start':0.0,'end':1.0}],dst)
        result=probe(dst)
        assert 0.8 < result['duration'] < 1.2, result
        assert result['width']==1280 and result['height']==720, result
        print('Media smoke test passed')

if __name__=='__main__':
    main()
