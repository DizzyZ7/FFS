import pytest
from app.visual_analysis import parse_signal_log,score_brightness,visual_scene_scores

def test_signalstats_metadata_parsing():
    text='lavfi.signalstats.YAVG=126.5\nnoise\nlavfi.signalstats.YAVG=100.0'
    assert parse_signal_log(text)==[126.5,100.0]

def test_exposure_scoring():
    assert score_brightness([128])==1
    assert score_brightness([0])==0
    assert score_brightness([])==0

def test_invalid_scene_rejected(tmp_path):
    with pytest.raises(ValueError):
        visual_scene_scores(tmp_path/'source.mp4',[{'start':4,'end':2}],duration=5)

def test_ffmpeg_command_and_result(tmp_path,monkeypatch):
    calls=[]
    def fake_run(command,**kwargs):
        calls.append(command)
        return type('Completed',(),{'returncode':0,'stderr':'lavfi.signalstats.YAVG=128'})()
    monkeypatch.setattr('app.visual_analysis.subprocess.run',fake_run)
    result=visual_scene_scores(tmp_path/'source.mp4',[{'start':0,'end':2}],duration=2)
    assert result[0]['brightness_score']==1
    assert result[0]['sample_count']==1
    assert 'signalstats,metadata=print' in calls[0][calls[0].index('-vf')+1]
