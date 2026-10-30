import pytest
from app import media

def test_social_rejects_bad_preset(tmp_path):
    with pytest.raises(ValueError):
        media.render_social(tmp_path/'video.mp4',[{'start':0,'end':1}],
                            tmp_path/'out.mp4',aspect='3:4')

def test_social_rejects_empty_timeline(tmp_path):
    with pytest.raises(ValueError):
        media.render_social(tmp_path/'video.mp4',[],tmp_path/'out.mp4')

def test_social_filtergraph_and_audio(tmp_path,monkeypatch):
    calls=[]
    def fake_run(args,timeout=180):
        calls.append(args)
        if args[0]=='ffprobe':
            if '-show_format' in args:
                return type('Result',(),{'stdout':'{"format":{"duration":"10"},"streams":[{"codec_type":"video","width":1920,"height":1080}]}'})()
            return type('Result',(),{'stdout':'{"streams":[{"codec_type":"audio"}]}'})()
        return type('Result',(),{'stdout':''})()
    monkeypatch.setattr(media,'run',fake_run)
    media.render_social(tmp_path/'source.mp4',[{'start':1,'end':3}],
                        tmp_path/'output.mp4',aspect='9:16')
    ffmpeg=calls[-1]
    graph=ffmpeg[ffmpeg.index('-filter_complex')+1]
    assert 'crop=720:1280' in graph
    assert 'atrim=start=1.0:end=3.0' in graph
    assert '[outa]' in ffmpeg
