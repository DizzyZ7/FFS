import pytest
from app.auto_edit import create_auto_edit_plan

def test_dynamic_plan_spreads_source_scenes():
    scenes=[{'start':i*5,'end':i*5+5} for i in range(8)]
    plan=create_auto_edit_plan(scenes,40,target_seconds=12)
    assert plan['estimated_seconds']==12
    assert plan['resolution']==(1080,1920)
    assert all(c['end']-c['start']<=3.001 for c in plan['clips'])
    assert len(set(c['source_index'] for c in plan['clips']))>=4
    assert len(plan['transitions'])==len(plan['clips'])-1

def test_empty_plan():
    assert create_auto_edit_plan([],10)['clips']==[]

@pytest.mark.parametrize('kwargs',[{'format':'bad'},{'pace':'fast'},{'target_seconds':1}])
def test_invalid_options(kwargs):
    with pytest.raises(ValueError):
        create_auto_edit_plan([{'start':0,'end':4}],4,**kwargs)

def test_no_clip_exceeds_source():
    plan=create_auto_edit_plan([{'start':0,'end':2}],2)
    assert plan['estimated_seconds']==2
