import pytest
from app.recreation import build_recreation_blueprint,revise_blueprint_shot

REFERENCE={'reference':{'width':1920,'height':1080,'fps':'30/1'},
 'shots':[{'id':'shot-0001','start':0,'end':2.5},
          {'id':'shot-0002','start':2.5,'end':5}]}

def test_blueprint_preserves_reference_cuts():
    blueprint=build_recreation_blueprint(REFERENCE,['person-1'],'Keep camera rhythm')
    assert blueprint['cut_points']==[2.5]
    assert blueprint['shots'][0]['subject_ids']==['person-1']
    assert blueprint['reference']['width']==1920
    assert blueprint['generation_available'] is False

def test_revision_only_changes_target_shot():
    original=build_recreation_blueprint(REFERENCE,['a'],'original')
    updated=revise_blueprint_shot(original,'shot-0002',instructions='new shot')
    assert original['shots'][1]['instructions']=='original'
    assert updated['shots'][0]==original['shots'][0]
    assert updated['shots'][1]['revision']==1
    assert updated['shots'][1]['instructions']=='new shot'

def test_invalid_reference_or_subjects():
    with pytest.raises(ValueError):
        build_recreation_blueprint({'shots':[]})
    with pytest.raises(ValueError):
        build_recreation_blueprint(REFERENCE,['x']*6)
