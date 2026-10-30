import copy
import pytest
from app.generation_payload import prepare_shot,assert_shot_not_stale

def sample():
    return {'reference':{'width':1080,'height':1920,'fps':'30/1'},
            'shots':[{'id':'shot-0001','duration':3.5,
            'source_start':1,'source_end':4.5,'instructions':'A red coat',
            'subject_ids':['subject-a'],'revision':0,'generation_status':'not_generated'}]}

def test_prepare_shot():
    prepared=prepare_shot(sample(),'abc','shot-0001')
    assert prepared.request.duration_seconds==3.5
    assert prepared.request.settings['reference_height']==1920
    assert assert_shot_not_stale(prepared,sample())

def test_revision_invalidates_prepared_request():
    blueprint=sample()
    prepared=prepare_shot(blueprint,'abc','shot-0001')
    modified=copy.deepcopy(blueprint)
    modified['shots'][0]['instructions']='Blue coat'
    with pytest.raises(ValueError,match='changed'):
        assert_shot_not_stale(prepared,modified)

def test_empty_prompt_rejected():
    blueprint=sample()
    blueprint['shots'][0]['instructions']=''
    with pytest.raises(ValueError):
        prepare_shot(blueprint,'abc','shot-0001')
