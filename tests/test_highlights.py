import pytest
from app.highlights import rank_highlights

def test_speech_scene_ranks_above_silence():
    scenes=[{'start':0,'end':5},{'start':5,'end':10}]
    words=[{'start':0.2,'end':1.5},{'start':1.5,'end':3.5}]
    ranked=rank_highlights(scenes,words,duration=10)
    assert ranked[0]['source_index']==0
    assert ranked[0]['signals']['speech_coverage']>0
    assert ranked[1]['signals']['speech_coverage']==0

def test_ranking_without_speech():
    ranked=rank_highlights([{'start':0,'end':2}],[],duration=2)
    assert len(ranked)==1

def test_bad_boundaries_rejected():
    with pytest.raises(ValueError):
        rank_highlights([{'start':5,'end':4}],[],duration=10)
