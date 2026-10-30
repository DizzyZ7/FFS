import pytest
from app.auto_edit import create_ranked_auto_edit_plan

def test_picks_highest_scoring_then_restores_source_order():
    scenes=[{'source_index':0,'start':0,'end':5,'score':0.2},
            {'source_index':1,'start':5,'end':10,'score':0.9},
            {'source_index':2,'start':10,'end':15,'score':0.8}]
    plan=create_ranked_auto_edit_plan(scenes,15,target_seconds=6)
    assert [x['source_index'] for x in plan['clips']]==[1,2]
    assert plan['estimated_seconds']==6
    assert len(plan['transitions'])==1

def test_invalid_score_rejected():
    with pytest.raises(ValueError):
        create_ranked_auto_edit_plan([{'source_index':0,'start':0,'end':2,'score':2}],2)

def test_no_speech_or_scenes():
    assert create_ranked_auto_edit_plan([],5)['clips']==[]
